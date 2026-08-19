"""One-off script to audit exactly what's in the S3 bucket - what folders
exist, how many files are in each, what file types are in each folder, and
whether anything looks unexpected (wrong extension, doesn't match the
naming pattern we assumed, etc)."""

from extract.s3_reader import list_files, BUCKET

# list_files with an empty prefix "" returns EVERY file in the whole bucket,
# not just Academy/ or Talent/ - this is how we see the full picture.
all_files = list_files(BUCKET, "")

print(f"Total files found in bucket: {len(all_files)}")
print()

# Group files by their top-level folder (the bit before the first "/")
folders = {}  # e.g. {"Academy": [...], "Talent": [...], "SomethingElse": [...]}

for key in all_files:
    if "/" in key:
        folder = key.split("/")[0]
    else:
        folder = "(no folder - file sits at the top level of the bucket)"

    if folder not in folders:
        folders[folder] = []

    folders[folder].append(key)

# Print a summary: one line per folder, showing how many files are in it
print("Folders found:")
for folder, files in folders.items():
    print(f"  {folder}: {len(files)} file(s)")
print()

# Show a few example filenames from each folder, so we can eyeball whether
# they match the naming pattern we expect
print("Sample filenames from each folder:")
for folder, files in folders.items():
    print(f"  {folder}:")
    for example in files[:5]:
        print(f"    {example}")
    if len(files) > 5:
        print(f"    ... and {len(files) - 5} more")
print()

# Break down file extensions PER FOLDER - this tells us if a folder we
# expected to be one file type (e.g. Talent/ = all .json) actually has a
# mix of different file types hiding in it
print("File types found in each folder:")
for folder, files in folders.items():
    extension_counts = {}  # e.g. {".json": 964, ".csv": 12, ".txt": 300}

    for key in files:
        # split on "." and grab the last piece as the extension
        if "." in key:
            extension = "." + key.split(".")[-1]
        else:
            extension = "(no extension)"

        if extension not in extension_counts:
            extension_counts[extension] = 0
        extension_counts[extension] += 1

    print(f"  {folder}:")
    for extension, count in extension_counts.items():
        print(f"    {extension}: {count} file(s)")
print()

# Check file extensions - flag anything that isn't .csv or .json, since
# that might mean something snuck in that our cleaning code isn't expecting
print("Checking for unexpected file extensions overall:")
unexpected_extensions = []

for key in all_files:
    if not (key.endswith(".csv") or key.endswith(".json")):
        unexpected_extensions.append(key)

if unexpected_extensions:
    print(f"  Found {len(unexpected_extensions)} file(s) that aren't .csv or .json:")
    for key in unexpected_extensions[:20]:
        print(f"    {key}")
    if len(unexpected_extensions) > 20:
        print(f"    ... and {len(unexpected_extensions) - 20} more")
else:
    print("  All files are .csv or .json - nothing unexpected.")