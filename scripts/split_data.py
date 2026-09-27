import os
from sklearn.model_selection import train_test_split
import shutil
import typer
from pathlib import Path
from typing import Optional, List, Dict

def copy(src: Path, dst: Path):
    """
    Copies a file from the source path to the destination path.

    Args:
    src: The source file path.
    dst: The destination file path..
    """
    if os.path.exists(src):
        shutil.copy(src, dst)


def copy_files(base_name: str, txt_files: Optional[Dict[str, Path]], rel_files: Optional[Dict[str, Path]], destination: Path):
    """
    Copies associated .txt and .rel files for a given base filename to the specified destination directory.

    Args:
        base_name: The base name of the file (without extension).
        txt_files: A dictionary mapping base filenames to .txt file paths.
        rel_files: A dictionary mapping base filenames to .rel file paths.
        destination: The directory where the files should be copied.
    """
    if txt_files:
        if txt_files[base_name]:
            copy(txt_files[base_name], destination)

    if rel_files:
        if rel_files[base_name]:
            copy(rel_files[base_name], destination)

def split(directory: Path, file_type: str, txt_directory: Optional[Path] = None, rel_directory: Optional[Path] = None):
    """
    Splits files of a given type in a directory into train, dev, and test sets,
    and optionally copies associated .txt and .rel files to the corresponding folders.

    Args:
        directory: The path to the directory containing the files to split.
        file_type: The file extension (without dot) to split (e.g., "iob", "ann").
        txt_directory: Directory containing .txt files to associate. Defaults to None.
        rel_directory: Directory containing .rel files to associate. Defaults to None.
    """
    txt_directory = Path(txt_directory) if txt_directory else None
    rel_directory = Path(rel_directory) if rel_directory else None

    files = list(directory.rglob(f'*.{file_type}'))
    txt_files = None
    if txt_directory:
        txt_files = {Path(f).stem: Path(f) for f in list(txt_directory.rglob('*.txt'))}
    rel_files = None
    if rel_directory:
        rel_files = {Path(f).stem: Path(f) for f in list(rel_directory.rglob('*.rel'))}
    
    if not files:
        print(f"No files found with extension .{file_type} in {directory}")
        return 
    
    train_files, temp_files = train_test_split(files, test_size=0.2, random_state=42)
    dev_files, test_files = train_test_split(temp_files, test_size=0.5, random_state=42)

    split_dirs = {name: Path(f"./{name}") for name in ["train", "dev", "test"]}

    for split_dir in split_dirs.values():
        split_dir.mkdir(parents=True, exist_ok=True)
    
    def process_files(file_list: List[Path], destination: Path):
        for file in file_list:
            base_name = file.stem
            copy(file, destination / file.name)
            if file_type in {"iob", "ann", "con"}:
                copy_files(base_name, txt_files, rel_files, destination)
    
    process_files(train_files, split_dirs["train"])
    process_files(dev_files, split_dirs["dev"])
    process_files(test_files, split_dirs["test"])

    print("train, dev, and test folders created successfully.")

def delete_split_folders():
    """
    Deletes train, dev and test folder 
    """
    for folder in ["./train", "./dev", "./test"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"Deleted folder: {folder}")
        else:
            print(f"Folder not found: {folder}")

if __name__ == "__main__":
    typer.run(split)