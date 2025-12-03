'use client';

import { useRef, useState, useCallback, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CameraIcon, RefreshCwIcon, CheckCircleIcon, XCircleIcon } from 'lucide-react';

interface CameraCaptureProps {
  onCapture: (imageBase64: string) => void;
  onVerificationResult?: (result: { is_match: boolean; similarity_score: number }) => void;
  title?: string;
  description?: string;
  showPreview?: boolean;
  autoStart?: boolean;
}

export function CameraCapture({
  onCapture,
  onVerificationResult,
  title = 'Face Verification',
  description = 'Position your face in the center of the frame',
  showPreview = true,
  autoStart = false,
}: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cameraActive, setCameraActive] = useState(false);

  const startCamera = useCallback(async () => {
    try {
      setError(null);
      setIsLoading(true);

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
      });

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        await videoRef.current.play();
      }

      setStream(mediaStream);
      setCameraActive(true);
      setCapturedImage(null);
    } catch (err) {
      console.error('Error accessing camera:', err);
      setError('Unable to access camera. Please ensure you have granted camera permissions.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    setCameraActive(false);
  }, [stream]);

  const captureImage = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    if (!context) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    context.drawImage(video, 0, 0);

    // Convert to base64
    const imageBase64 = canvas.toDataURL('image/jpeg', 0.8);

    // Remove the data URL prefix to get just the base64 string
    const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');

    setCapturedImage(imageBase64);
    onCapture(base64Data);

    // Stop camera after capture
    stopCamera();
  }, [onCapture, stopCamera]);

  const retake = useCallback(() => {
    setCapturedImage(null);
    startCamera();
  }, [startCamera]);

  // Auto-start camera if enabled
  useEffect(() => {
    if (autoStart) {
      startCamera();
    }

    return () => {
      stopCamera();
    };
  }, [autoStart]);

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CameraIcon className="h-5 w-5" />
          {title}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
            <XCircleIcon className="h-5 w-5" />
            <span>{error}</span>
          </div>
        )}

        <div className="relative aspect-video bg-gray-900 rounded-lg overflow-hidden">
          {!cameraActive && !capturedImage && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Button onClick={startCamera} disabled={isLoading} size="lg">
                {isLoading ? (
                  <>
                    <RefreshCwIcon className="h-4 w-4 mr-2 animate-spin" />
                    Starting Camera...
                  </>
                ) : (
                  <>
                    <CameraIcon className="h-4 w-4 mr-2" />
                    Start Camera
                  </>
                )}
              </Button>
            </div>
          )}

          {capturedImage && showPreview ? (
            <img
              src={capturedImage}
              alt="Captured"
              className="w-full h-full object-cover"
            />
          ) : (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover ${!cameraActive ? 'hidden' : ''}`}
            />
          )}

          {/* Face guide overlay */}
          {cameraActive && !capturedImage && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="w-48 h-60 border-2 border-white/50 rounded-full" />
            </div>
          )}
        </div>

        {/* Hidden canvas for capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Action buttons */}
        <div className="flex gap-2">
          {cameraActive && !capturedImage && (
            <>
              <Button onClick={captureImage} className="flex-1">
                <CameraIcon className="h-4 w-4 mr-2" />
                Capture Photo
              </Button>
              <Button variant="outline" onClick={stopCamera}>
                Cancel
              </Button>
            </>
          )}

          {capturedImage && (
            <>
              <Button variant="outline" onClick={retake} className="flex-1">
                <RefreshCwIcon className="h-4 w-4 mr-2" />
                Retake
              </Button>
              <Button className="flex-1">
                <CheckCircleIcon className="h-4 w-4 mr-2" />
                Use This Photo
              </Button>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default CameraCapture;
