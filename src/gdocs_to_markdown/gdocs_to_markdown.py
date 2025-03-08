import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import TOKEN_FILE_PATH, SCOPES, CREDENTIALS_FILE_PATH
from googleapiclient.discovery import build, Resource
from typing import List, Optional

from pathlib import Path

from pydantic import BaseModel, computed_field

from string import punctuation


class GoogleDriveFolder(BaseModel):
    id: str = None
    name: str = None
    documents: List["GoogleDriveDocument"] = None
    subfolders: List["GoogleDriveFolder"] = None

    @computed_field
    @property
    def local_folder_name(self) -> str:
        """
        As Google Drive allows the use of special characters in the folder name, this function removes them,
        making it a valid folder name.
        :return: folder name cleaned up from special characters
        """
        translator = str.maketrans("", "", punctuation)
        return self.name.translate(translator)


class GoogleDriveDocument(BaseModel):
    id: str = None
    name: str = None
    modifiedTime: Optional[str] = None
    description: Optional[str] = None
    markdown_body: Optional[bytes] = None
    google_docs_url: Optional[str] = None
    lastModifyingUser: Optional[dict] = None

    # Here multiple other metadata points can be defined and collected from each of the document that is in Drive.
    # Google APIs will also return multiple information as, for example, a public link to the user's profile picture
    # (icon) which can be passed in the markdown header and further on be displayed in

    @property
    def modified_time(self) -> str:
        return self.modifiedTime

    @computed_field
    @property
    def markdown_header(self) -> str:
        """
        Compute the header of the markdown file, given all the metadata that has been saved when downloading it
        from Google.
        :return: markdown metadata header
        """
        return f"""---
title: {self.name}
description: {self.description}
updated: {self.modified_time}
lastModifyingUser: {self.lastModifyingUser.get("displayName").split(" ")[0]}
---

"""

    @computed_field
    @property
    def local_file_name(self) -> str:
        """
        As Google Docs allows the use of special characters in the document names, this function removes them,
        making it a valid name for a file.
        :return: file name cleaned up from special characters
        """
        translator = str.maketrans("", "", punctuation)
        return self.name.translate(translator)


class GoogleDocs2Markdown:
    creds: Credentials

    scopes = SCOPES
    token_file_path = TOKEN_FILE_PATH
    credentials_file_path = CREDENTIALS_FILE_PATH

    service: Resource

    # This class does not handle the automatic refresh of the credentials, it's a possible improvement

    def __init__(self):
        self.creds = self.get_or_generate_credentials()
        self.service = build("drive", "v3", credentials=self.creds)

    def get_or_generate_credentials(self):
        creds = None

        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.

        if os.path.exists(self.token_file_path):
            creds = Credentials.from_authorized_user_file(
                self.token_file_path, self.scopes
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file_path, self.scopes
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_file_path, "w") as token:
                token.write(creds.to_json())

        return creds

    def get_document_markdown_content(self, document_id) -> GoogleDriveDocument:
        # Google allows downloading (and uploading) the content of files by specifying the format that you need in the
        # request via the mimeType parameter
        # https://developers.google.com/drive/api/guides/mime-types
        # https://news.ycombinator.com/item?id=40982118
        data = (
            self.service.files()
            .export(fileId=document_id, mimeType="text/markdown")
            .execute()
        )
        return data

    def get_folder_structure_given_root(self, folder_id) -> GoogleDriveFolder:
        folder_name_request = (
            self.service.files().get(fileId=folder_id, fields="name").execute()
        )
        folder_name = folder_name_request.get("name")

        # The following are useful documentation links that contain references to the possible values that can be
        # requested via the 'fields' parameter for the files / folders that get retrieved by the query via the 'q'
        # (query) parameter
        # https://developers.google.com/drive/api/reference/rest/v3/files#File
        # https://developers.google.com/drive/api/reference/rest/v3/files/list?apix=true
        # https://developers.google.com/drive/api/guides/search-files#python
        documents_request = (
            self.service.files()
            .list(
                q="mimeType='application/vnd.google-apps.document' and parents in '"
                + folder_id
                + "' and trashed = false",
                fields="nextPageToken, files(id, name, description, modifiedTime, lastModifyingUser, owners, version, properties, permissionIds)",
                pageSize=400,
            )
            .execute()
        )

        documents = []
        for document in documents_request["files"]:
            print(f"Found document: {document}")
            documents.append(
                GoogleDriveDocument(
                    **document,
                    markdown_body=self.get_document_markdown_content(
                        document_id=document.get("id")
                    ),
                )
            )

        subfolders_request = (
            self.service.files()
            .list(
                q="mimeType='application/vnd.google-apps.folder' and parents in '"
                + folder_id
                + "' and trashed = false",
                fields="nextPageToken, files(id, name, owners)",
                pageSize=400,
            )
            .execute()
        )

        subfolders = []
        for subfolder in subfolders_request["files"]:
            print(f"Found subfolder: {subfolder}")
            subfolders.append(
                self.get_folder_structure_given_root(folder_id=subfolder.get("id"))
            )

        return GoogleDriveFolder(
            id=folder_id, name=folder_name, documents=documents, subfolders=subfolders
        )

    def save_folder_structure_in_path(
        self, folder: GoogleDriveFolder, parent_folder_path: Path
    ):
        current_main_folder = parent_folder_path.joinpath(folder.local_folder_name)

        if len(folder.documents):
            os.makedirs(current_main_folder, exist_ok=True)

        for document in folder.documents:
            full_file_path = Path(
                f"{current_main_folder}/{document.local_file_name}.md"
            )
            print(f"Downloading {full_file_path}")

            with Path.open(full_file_path, "wb") as md_file:
                md_file.write(str.encode(document.markdown_header) + document.markdown_body)

        for subfolder in folder.subfolders:
            self.save_folder_structure_in_path(subfolder, current_main_folder)
