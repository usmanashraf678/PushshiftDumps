This repo contains example python scripts for processing the reddit dump files created by pushshift. The files can be downloaded from [here](https://files.pushshift.io/reddit/) or torrented from [here](https://academictorrents.com/details/f37bb9c0abe350f0f1cbd4577d0fe413ed07724e).

* `single_file.py` decompresses and iterates over a single zst compressed file
* `iterate_folder.py` does the same, but for all files in a folder
* `combine_folder_multiprocess.py` uses separate processes to iterate over multiple files in parallel, writing lines that match the criteria passed in to text files, then combining them into a final zst compressed file