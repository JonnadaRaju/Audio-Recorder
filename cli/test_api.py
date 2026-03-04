import typer
import requests
import time

BASE_URL = "http://localhost:8000"

cli = typer.Typer()


@cli.callback()
def main():
    """CLI entrypoint for API acceptance tests."""


class TestResult:
    def __init__(self, name: str, passed: bool, status_code: int, response: str):
        self.name = name
        self.passed = passed
        self.status_code = status_code
        self.response = response

    def print_result(self):
        status = "PASS" if self.passed else "FAIL"
        typer.echo(f"[{status}] {self.name}")
        typer.echo(f"  Status Code: {self.status_code}")
        typer.echo(f"  Response: {self.response[:200]}...")
        typer.echo("")


results: list[TestResult] = []
TEST_EMAIL = f"test{int(time.time())}@example.com"
TEST_PASSWORD = "testpass123"


def record_test(name: str, passed: bool, status_code: int, response: str):
    results.append(TestResult(name, passed, status_code, response))
    if not passed:
        typer.echo(f"ERROR: Test '{name}' failed!", err=True)


def test_valid_registration():
    url = f"{BASE_URL}/auth/register"
    data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    try:
        r = requests.post(url, json=data)
        passed = r.status_code == 201
        record_test("Valid Registration", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Valid Registration", False, 0, str(e))
        return False


def test_duplicate_registration():
    url = f"{BASE_URL}/auth/register"
    data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    try:
        r = requests.post(url, json=data)
        passed = r.status_code == 400
        record_test("Duplicate Registration", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Duplicate Registration", False, 0, str(e))
        return False


def test_invalid_authentication():
    url = f"{BASE_URL}/auth/login"
    try:
        r = requests.post(url, json={"email": "wrong@example.com", "password": "wrongpass"})
        passed = r.status_code == 401
        record_test("Invalid Authentication", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Invalid Authentication", False, 0, str(e))
        return False


def test_valid_login():
    url = f"{BASE_URL}/auth/login"
    try:
        r = requests.post(url, json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        passed = r.status_code == 200 and "access_token" in r.json()
        if passed:
            token = r.json()["access_token"]
            record_test("Valid Login", True, r.status_code, r.text)
            return token
        record_test("Valid Login", False, r.status_code, r.text)
        return None
    except Exception as e:
        record_test("Valid Login", False, 0, str(e))
        return None


def test_missing_token():
    url = f"{BASE_URL}/recordings"
    try:
        r = requests.get(url)
        passed = r.status_code == 401
        record_test("Missing Token", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Missing Token", False, 0, str(e))
        return False


def test_upload_without_auth():
    url = f"{BASE_URL}/recordings/upload"
    try:
        files = {"file": ("test.webm", b"fake audio data", "audio/webm")}
        r = requests.post(url, files=files)
        passed = r.status_code == 401
        record_test("Upload Without Auth", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Upload Without Auth", False, 0, str(e))
        return False


def test_invalid_file_upload(token: str):
    url = f"{BASE_URL}/recordings/upload"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        files = {"file": ("test.txt", b"not audio", "text/plain")}
        r = requests.post(url, files=files, headers=headers)
        passed = r.status_code == 400
        record_test("Invalid File Upload", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Invalid File Upload", False, 0, str(e))
        return False


def test_list_recordings(token: str):
    url = f"{BASE_URL}/recordings"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(url, headers=headers)
        passed = r.status_code == 200 and isinstance(r.json(), list)
        record_test("List Recordings", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("List Recordings", False, 0, str(e))
        return False


def test_upload_audio(token: str):
    url = f"{BASE_URL}/recordings/upload"
    headers = {"Authorization": f"Bearer {token}"}
    audio_data = b"fake audio data for testing"
    try:
        files = {"file": ("test_recording.webm", audio_data, "audio/webm")}
        data = {"duration": 10}
        r = requests.post(url, files=files, data=data, headers=headers)
        passed = r.status_code == 201
        if passed:
            recording_id = r.json()["id"]
            record_test("Upload Audio", True, r.status_code, r.text)
            return recording_id
        record_test("Upload Audio", False, r.status_code, r.text)
        return None
    except Exception as e:
        record_test("Upload Audio", False, 0, str(e))
        return None


def test_get_recording(token: str, recording_id: int):
    url = f"{BASE_URL}/recordings/{recording_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(url, headers=headers)
        passed = r.status_code == 200
        record_test("Get Recording", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Get Recording", False, 0, str(e))
        return False


def test_get_nonexistent_recording(token: str):
    url = f"{BASE_URL}/recordings/999999"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(url, headers=headers)
        passed = r.status_code == 404
        record_test("Get Non-existent Recording", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Get Non-existent Recording", False, 0, str(e))
        return False


def test_stream_recording(token: str, recording_id: int):
    url = f"{BASE_URL}/recordings/{recording_id}/stream"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(url, headers=headers)
        passed = r.status_code == 200
        record_test("Stream Recording", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Stream Recording", False, 0, str(e))
        return False


def test_unauthorized_access():
    url = f"{BASE_URL}/recordings"
    try:
        r = requests.get(url, headers={"Authorization": "Bearer wrong_token"})
        passed = r.status_code == 401
        record_test("Unauthorized Access", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Unauthorized Access", False, 0, str(e))
        return False


def test_delete_recording(token: str, recording_id: int):
    url = f"{BASE_URL}/recordings/{recording_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.delete(url, headers=headers)
        passed = r.status_code == 204
        record_test("Delete Recording", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Delete Recording", False, 0, str(e))
        return False


def test_delete_nonexistent_recording(token: str):
    url = f"{BASE_URL}/recordings/999999"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.delete(url, headers=headers)
        passed = r.status_code == 404
        record_test("Delete Non-existent Recording", passed, r.status_code, r.text)
        return passed
    except Exception as e:
        record_test("Delete Non-existent Recording", False, 0, str(e))
        return False


@cli.command("run-tests")
def run_tests():
    typer.echo("=" * 50)
    typer.echo("Running Audio Recorder API Tests")
    typer.echo("=" * 50)
    typer.echo("")

    test_valid_registration()
    test_duplicate_registration()
    test_invalid_authentication()
    token = test_valid_login()
    
    if not token:
        typer.echo("Cannot proceed without valid login token!", err=True)
        print_summary()
        raise typer.Exit(code=1)
    
    test_missing_token()
    test_upload_without_auth()
    test_invalid_file_upload(token)
    test_list_recordings(token)
    recording_id = test_upload_audio(token)
    
    if not recording_id:
        typer.echo("Cannot proceed without uploaded recording!", err=True)
        print_summary()
        raise typer.Exit(code=1)
    
    test_get_recording(token, recording_id)
    test_get_nonexistent_recording(token)
    test_stream_recording(token, recording_id)
    test_unauthorized_access()
    test_delete_recording(token, recording_id)
    test_delete_nonexistent_recording(token)

    print_summary()


def print_summary():
    typer.echo("")
    typer.echo("=" * 50)
    typer.echo("TEST SUMMARY")
    typer.echo("=" * 50)
    
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    
    for r in results:
        r.print_result()
    
    typer.echo(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    
    if failed > 0:
        typer.echo("OVERALL: FAIL", err=True)
        raise typer.Exit(code=1)
    else:
        typer.echo("OVERALL: PASS")


if __name__ == "__main__":
    cli()
