from typing import Sequence

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
import time

GOOGLE_APPS_FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'


def main():
    auth = GoogleAuth()
    auth.CommandLineAuth()
    drive = GoogleDrive(auth)

    print("***** Pydrive upload test *****")
    print("Trying to get folder Camguard from root")
    folders: Sequence[GoogleDriveFile] = search_folder(drive, "Camguard")
    folder_id: str = ""
    folder_name: str = "Camguard"
    if not folders:
        print(f"Creating folder {folder_name}")
        created_folder = drive.CreateFile({
            'title': folder_name,
            'mimeType': GOOGLE_APPS_FOLDER_MIMETYPE
        })
        created_folder.Upload()
        folder_id = created_folder['id']
    else:
        if len(folders) > 1:
            raise FileNotFoundError("Multiple root directories were found")
        folder_id = folders[0]['id']
        print(f"Found folder {folder_name} with id: {folder_id}")

    file_name = 'upload.jpeg'
    files: Sequence[GoogleDriveFile] = search_file(drive, file_name)
    file: GoogleDriveFile = None

    if not files:
        file = drive.CreateFile({
            'title': file_name,
            'parents': [{'id': folder_id}]
        })
    else:
        if len(folders) > 1:
            raise FileNotFoundError("Multiple upload files")
        file = files[0]
        print(f"Found file '{file.metadata['title']}' on gdrive")

    start_time = time.time()

    test_file_path: str = "/home/matthias/Pictures/test2.jpeg"
    print(
        f"Uploading test file '{test_file_path}' to '{folder_name}/{file_name}'")
    file.SetContentFile(test_file_path)
    file.Upload()

    end_time = time.time()
    print(f"Took {round(end_time - start_time, 2)}[s]")


def search_file(drive: GoogleDrive,
                file_name: str,
                parent_folder_id: str = None) -> Sequence[GoogleDriveFile]:
    parent_query: str = ""
    if parent_folder_id:
        parent_query = f"and '{parent_folder_id}' in parents"

    return drive.ListFile({
        'q': f"title='{file_name}' "
        f"{parent_query} "
        "and trashed=false"
    }).GetList()


def search_folder(drive: GoogleDrive, folder_name: str) -> Sequence[GoogleDriveFile]:
    return drive.ListFile({
        'q': f"title='{folder_name}' "
        f"and mimeType='{GOOGLE_APPS_FOLDER_MIMETYPE}' "
        "and trashed=false"
    }).GetList()


if __name__ == "__main__":
    main()
