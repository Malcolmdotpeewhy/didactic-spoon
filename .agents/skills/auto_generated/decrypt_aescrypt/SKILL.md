---
name: Decrypt AESCrypt Files
description: Automatically identify, install dependencies for, and decrypt .aes (AESCrypt) format files using a python script or GUI.
---

# Decrypt AESCrypt Files

## Overview
This skill provides the capability to decrypt files encrypted with the AESCrypt format (`.aes`). 

## Dependencies
- Package: `pyAesCrypt`
- Command to install: `py -m pip install pyAesCrypt`

## Execution Pattern

1. **Verify Format:** Use `Get-Content -Encoding Byte` or a simple python script to check if the file starts with the AESCrypt magic bytes (`AES\x02\x00\x00`).
2. **Install Library:** Ensure `pyAesCrypt` is installed via pip.
3. **Decrypt:** 
   - Write a python script using `pyAesCrypt.decryptFile(input_file, output_file, password, bufferSize)`
   - If interactive, generate a quick Tkinter GUI or use `getpass` to prompt the user for the password safely.

## Example CLI Script
```python
import pyAesCrypt
bufferSize = 64 * 1024
password = "your_password"
pyAesCrypt.decryptFile("file.txt.aes", "file.txt", password, bufferSize)
```
