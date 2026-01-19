import httpx
import sys
import os

def verify_study_import(study_id: str, token: str, base_url: str):
    """
    Verifies that a study has been imported correctly by checking its chapter count.
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{base_url}/api/v1/workspace/studies/{study_id}"

    print(f"Verifying study import for study_id: {study_id}")
    print(f"Calling GET {url}")

    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

            data = response.json()
            study_data = data.get("study", {})
            chapter_count = study_data.get("chapter_count")
            chapters = data.get("chapters", [])
            
            print(f"Response status code: {response.status_code}")
            print(f"Study title: '{study_data.get('title')}'")
            print(f"Reported chapter_count: {chapter_count}")
            print(f"Actual number of chapters returned: {len(chapters)}")

            if chapter_count is not None and chapter_count > 0 and len(chapters) == chapter_count:
                print("\nSUCCESS: Study contains chapters.")
                # Further check chapter statuses
                processing_chapters = [c for c in chapters if c.get('pgn_status') == 'processing']
                ready_chapters = [c for c in chapters if c.get('pgn_status') == 'ready']
                print(f" - {len(ready_chapters)} chapters are 'ready'")
                print(f" - {len(processing_chapters)} chapters are 'processing'")
                if len(processing_chapters) > 0:
                    print("NOTE: Some chapters are still processing in the background, which is expected.")
            else:
                print(f"\nFAILURE: Study chapter count is not valid. Count: {chapter_count}, Chapters found: {len(chapters)}")
                sys.exit(1)

    except httpx.HTTPStatusError as e:
        print(f"\nERROR: HTTP error occurred: {e}")
        print(f"Response content: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_import.py <study_id> <auth_token>")
        sys.exit(1)

    study_id_arg = sys.argv[1]
    auth_token_arg = sys.argv[2]
    
    # Allow overriding base_url via environment variable, default to localhost
    api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

    verify_study_import(study_id=study_id_arg, token=auth_token_arg, base_url=api_base_url)
