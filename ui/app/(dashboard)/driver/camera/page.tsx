"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { VideoIcon, VideoOffIcon, CheckCircleIcon } from "lucide-react";

export default function DriverCameraPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [streaming, setStreaming] = useState(false);
  const [vehicleId, setVehicleId] = useState("1");
  const [framesSent, setFramesSent] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const startCamera = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: 640, height: 480 },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setStreaming(true);
        startSendingFrames();
      }
    } catch (err) {
      console.error("Camera error:", err);
      setError("Could not access camera. Please allow camera permissions.");
    }
  };

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setStreaming(false);
  };

  const startSendingFrames = () => {
    // Send a frame every 500ms (2 FPS for demo)
    intervalRef.current = setInterval(() => {
      sendFrame();
    }, 500);
  };

  const sendFrame = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext("2d");

    if (!ctx) return;

    // Draw video frame to canvas
    canvas.width = 640;
    canvas.height = 480;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Add timestamp overlay
    ctx.fillStyle = "rgba(0, 0, 0, 0.5)";
    ctx.fillRect(10, canvas.height - 40, 200, 30);
    ctx.fillStyle = "white";
    ctx.font = "14px monospace";
    ctx.fillText(new Date().toLocaleTimeString(), 20, canvas.height - 18);

    // Convert to blob and send
    canvas.toBlob(
      async (blob) => {
        if (!blob) return;

        try {
          const routeId = `taxi-${vehicleId.padStart(2, "0")}`;

          await fetch("http://localhost:8000/api/v1/video/device/upload", {
            method: "POST",
            headers: {
              "Content-Type": "image/jpeg",
              "X-Route-ID": routeId,
            },
            body: blob,
          });

          setFramesSent((prev) => prev + 1);
        } catch (err) {
          console.error("Failed to send frame:", err);
        }
      },
      "image/jpeg",
      0.7
    );
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="max-w-lg mx-auto p-4">
      <h1 className="text-2xl font-bold mb-2">Mock Camera</h1>
      <p className="text-gray-500 mb-6">
        Simulates ESP32-CAM sending video to the server
      </p>

      {/* Vehicle ID selector */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Vehicle ID</label>
        <select
          value={vehicleId}
          onChange={(e) => setVehicleId(e.target.value)}
          className="w-full p-2 border rounded-lg"
          disabled={streaming}
        >
          {[1, 2, 3, 4, 5, 6, 7, 8].map((id) => (
            <option key={id} value={id}>
              Vehicle #{id} (taxi-{id.toString().padStart(2, "0")})
            </option>
          ))}
        </select>
      </div>

      {/* Camera preview */}
      <div className="bg-black rounded-lg overflow-hidden mb-4 aspect-video relative">
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          playsInline
          muted
        />
        {!streaming && (
          <div className="absolute inset-0 flex items-center justify-center text-white">
            <VideoOffIcon className="w-16 h-16 opacity-50" />
          </div>
        )}
        {streaming && (
          <div className="absolute top-3 left-3 bg-red-600 text-white px-2 py-1 rounded text-xs font-bold flex items-center gap-1">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
            STREAMING
          </div>
        )}
      </div>

      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Error message */}
      {error && (
        <div className="bg-red-100 text-red-700 p-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Controls */}
      <div className="space-y-3">
        {!streaming ? (
          <Button
            className="w-full h-14 text-lg bg-green-600 hover:bg-green-700"
            onClick={startCamera}
          >
            <VideoIcon className="w-5 h-5 mr-2" />
            Start Camera
          </Button>
        ) : (
          <Button
            className="w-full h-14 text-lg bg-red-600 hover:bg-red-700"
            onClick={stopCamera}
          >
            <VideoOffIcon className="w-5 h-5 mr-2" />
            Stop Camera
          </Button>
        )}
      </div>

      {/* Stats */}
      {streaming && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg">
          <div className="flex items-center gap-2 text-green-700">
            <CheckCircleIcon className="w-5 h-5" />
            <span className="font-medium">Streaming to server</span>
          </div>
          <p className="text-sm text-green-600 mt-1">
            Frames sent: {framesSent}
          </p>
          <p className="text-sm text-green-600">
            Route ID: taxi-{vehicleId.padStart(2, "0")}
          </p>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-6 p-4 bg-gray-100 rounded-lg text-sm text-gray-600">
        <p className="font-medium mb-2">How it works:</p>
        <ol className="list-decimal list-inside space-y-1">
          <li>Select the vehicle ID for this camera</li>
          <li>Click "Start Camera" to begin streaming</li>
          <li>Frames are sent to the server every 500ms</li>
          <li>Customer will see live feed on their trip page</li>
        </ol>
      </div>
    </div>
  );
}
