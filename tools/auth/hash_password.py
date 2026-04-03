#!/usr/bin/env python3
from passlib.hash import bcrypt
import getpass
pw = getpass.getpass("Password to hash: ")
print(bcrypt.hash(pw))
