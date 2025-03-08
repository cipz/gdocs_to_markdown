from gdocs_to_markdown.gdocs_to_markdown import GoogleDocs2Markdown
from pathlib import Path


def main():
    gdtm = GoogleDocs2Markdown()

    # Before running, add at least a folder in the following list.
    # In this case, download_path refers to the absolute path where the MkDocs container is mounted.
    # The folders can be loaded from a configuration file in JSON / YAML.
    folders_to_sync = [
        {
            "folder_id": "",  # Google Drive folder ID
            "download_path": "",  # where the markdown content will be downloaded
        },
    ]

    for folder in folders_to_sync:
        print(f"Parsing folder with id {folder.get('folder_id')}")
        folder_structure = gdtm.get_folder_structure_given_root(
            folder_id=folder.get("folder_id")
        )
        print(f"Downloading files locally in {folder.get('download_path')}")
        gdtm.save_folder_structure_in_path(folder_structure, Path(folder.get("download_path")))


if __name__ == "__main__":
    main()
