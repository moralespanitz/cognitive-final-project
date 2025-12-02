"""
Mock Face Recognition Service.
Simulates facial recognition for demo purposes without AWS Rekognition.
"""

import random
import hashlib
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of face verification."""
    is_match: bool
    similarity_score: int  # 0-100
    user_id: Optional[int] = None
    message: str = ""


class FaceRecognitionService:
    """
    Mock face recognition service.
    Simulates face matching behavior for demo purposes.
    """

    # In-memory storage for face data (simulates Rekognition collection)
    _face_collection: Dict[int, str] = {}

    # Configurable similarity threshold (0-100)
    _similarity_threshold: int = 80

    @classmethod
    def set_similarity_threshold(cls, threshold: int) -> None:
        """Set the similarity threshold for face matching."""
        cls._similarity_threshold = max(0, min(100, threshold))
        logger.info(f"Similarity threshold set to {cls._similarity_threshold}%")

    @classmethod
    def get_similarity_threshold(cls) -> int:
        """Get the current similarity threshold."""
        return cls._similarity_threshold

    @classmethod
    def register_face(cls, user_id: int, face_image_base64: str) -> Dict[str, Any]:
        """
        Register a face for a user.

        Args:
            user_id: The user's ID
            face_image_base64: Base64 encoded face image

        Returns:
            Registration result with face_id
        """
        # Generate a mock face encoding (hash of the image)
        face_encoding = cls._generate_face_encoding(face_image_base64)

        # Store in collection
        cls._face_collection[user_id] = face_encoding

        logger.info(f"Face registered for user {user_id}")

        return {
            "success": True,
            "user_id": user_id,
            "face_id": f"face_{user_id}_{face_encoding[:8]}",
            "message": "Face registered successfully"
        }

    @classmethod
    def verify_face(cls, user_id: int, face_image_base64: str) -> VerificationResult:
        """
        Verify a face against a registered user.

        Args:
            user_id: The user's ID to verify against
            face_image_base64: Base64 encoded face image to verify

        Returns:
            VerificationResult with match status and similarity score
        """
        # Check if user has registered face
        if user_id not in cls._face_collection:
            return VerificationResult(
                is_match=False,
                similarity_score=0,
                user_id=user_id,
                message="No registered face found for this user"
            )

        # Generate encoding for verification image
        verification_encoding = cls._generate_face_encoding(face_image_base64)
        registered_encoding = cls._face_collection[user_id]

        # Calculate mock similarity (for demo, use encoding similarity + randomness)
        similarity_score = cls._calculate_similarity(registered_encoding, verification_encoding)

        # Determine if it's a match based on threshold
        is_match = similarity_score >= cls._similarity_threshold

        message = "Face verified successfully" if is_match else "Face verification failed"

        logger.info(f"Face verification for user {user_id}: {is_match} (score: {similarity_score}%)")

        return VerificationResult(
            is_match=is_match,
            similarity_score=similarity_score,
            user_id=user_id,
            message=message
        )

    @classmethod
    def search_face(cls, face_image_base64: str) -> Optional[VerificationResult]:
        """
        Search for a matching face in the collection.

        Args:
            face_image_base64: Base64 encoded face image to search

        Returns:
            VerificationResult if match found, None otherwise
        """
        if not cls._face_collection:
            return None

        verification_encoding = cls._generate_face_encoding(face_image_base64)

        best_match = None
        best_score = 0

        for user_id, registered_encoding in cls._face_collection.items():
            similarity = cls._calculate_similarity(registered_encoding, verification_encoding)
            if similarity > best_score and similarity >= cls._similarity_threshold:
                best_score = similarity
                best_match = user_id

        if best_match is not None:
            return VerificationResult(
                is_match=True,
                similarity_score=best_score,
                user_id=best_match,
                message="Face match found"
            )

        return None

    @classmethod
    def delete_face(cls, user_id: int) -> bool:
        """
        Remove a face from the collection.

        Args:
            user_id: The user's ID

        Returns:
            True if removed, False if not found
        """
        if user_id in cls._face_collection:
            del cls._face_collection[user_id]
            logger.info(f"Face removed for user {user_id}")
            return True
        return False

    @classmethod
    def has_registered_face(cls, user_id: int) -> bool:
        """Check if a user has a registered face."""
        return user_id in cls._face_collection

    @classmethod
    def get_registered_users(cls) -> list:
        """Get list of user IDs with registered faces."""
        return list(cls._face_collection.keys())

    @classmethod
    def get_collection_count(cls) -> int:
        """Get the number of registered faces."""
        return len(cls._face_collection)

    @staticmethod
    def _generate_face_encoding(image_base64: str) -> str:
        """
        Generate a mock face encoding from an image.
        In real implementation, this would extract facial features.
        """
        # Use hash of image data as mock encoding
        return hashlib.sha256(image_base64.encode()).hexdigest()

    @staticmethod
    def _calculate_similarity(encoding1: str, encoding2: str) -> int:
        """
        Calculate mock similarity between two face encodings.

        For demo purposes:
        - Same encoding = 95-100% match
        - Different encoding = 60-90% match (simulates real-world variance)
        """
        if encoding1 == encoding2:
            # Same image - high similarity with slight variance
            return random.randint(95, 100)
        else:
            # Different images - moderate similarity with variance
            # In a real system, this would compare facial feature vectors
            # For demo, we simulate "same person, different photo" vs "different person"
            # We'll use hash comparison to add some determinism

            # Compare first 8 chars of hash to add some consistency
            common_chars = sum(1 for a, b in zip(encoding1[:8], encoding2[:8]) if a == b)

            # Base similarity on common chars (0-8)
            base_similarity = 50 + (common_chars * 5)  # 50-90 base range

            # Add randomness for realistic variance
            variance = random.randint(-10, 10)

            return max(0, min(100, base_similarity + variance))


# Singleton instance
face_recognition_service = FaceRecognitionService()
