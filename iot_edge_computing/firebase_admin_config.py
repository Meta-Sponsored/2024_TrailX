"""The module handles Google Cloud Firebase Admin SDK with credentials."""

import os
import firebase_admin
from firebase_admin import credentials, firestore

FIREBASE_ADMIN_SDK_PATH="/home/trailx/Desktop/keys/gix-trailx-firebase-adminsdk-z0gyx-72d32dbfc4.json"

def initialize_firebase_admin():
    """
    Initializes the Firebase Admin SDK with credentials from
    an environment variable and returns a Firestore client.

    This function first retrieves the path to the Firebase Admin SDK JSON
    credentials file from an environment variable named 'FIREBASE_ADMIN_SDK_PATH'.
    It then initializes the Firebase Admin SDK with these credentials.
    This initialization is required to authenticate and
    interact with Firebase services programmatically.
    Once the Firebase Admin SDK is initialized,
    the function creates and returns a Firestore client.
    This client can be used to interact with the
    Firestore database, allowing the application to perform operations
    such as reading from and writing to the database.

    Returns:
        firestore.Client: A Firestore client instance that
        can be used to interact with the Firestore database.
    """
    try:
        cred = credentials.Certificate(FIREBASE_ADMIN_SDK_PATH)

        # Initialize the Firebase Admin SDK with the loaded credentials
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        # Create and return a Firestore client instance
        return firestore.client()
    except Exception as e:
        print(f"Failed to initialize Firebase Admin SDK: {e}")
        return None
