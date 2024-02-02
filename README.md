# Overview

This repo has been adapted from the original [Pushshift Dumps repo](https://github.com/Watchful1/PushshiftDumps) to extract IDs of all posts made in a subreddit from the beginning of its creation. This repo is based on the Push Shifts Dumps available via academic torrents [here](https://academictorrents.com/details/c398a571976c78d346c325bd75c47b82edf6124e). This torrent has aggregated top 20k subreddits (by comments and posts) as separate zst files. Using this repo, any subreddit can be processed (using its zst file) to get the IDs of all posts made in that subreddit.

## How to download the relevant subreddit zst file?

1. In order to download the zst files, you would need to use a torrent client. I used qBittorrent for this. You can download qBittorrent [here](https://www.qbittorrent.org/download).
2. Once you have that installed, go to the torrent link and click download, this will download a small ".torrent" file.
3. In qBittorrent, click the plus at the top and select this torrent file. This will open the list of all the subreddits. Click "Select None" to unselect everything, then use the filter box in the top right to search for the subreddit you want. Select the files you're interested in, there's a separate one for the comments and submissions of each subreddit, then click okay. The files will then be downloaded.
4. We'll only be needing the submissions file for our purposes to get the IDs of all posts made in a subreddit. For example, `subreddits/Instagram_submissions.zst` is the file for the Instagram subreddit. The post details (e.g. timestamp, title, caption, comments etc.) are extracted uing the PRAW library. We'll only be using the the Push Shift Dump library to get the IDs which work as a seed for the extraction process.

## How to use this repo to extract IDs of all posts made in a subreddit?

Step 0: Before running the script, the input files (zst submissions files download from the torrent link) should be placed in the `zst_files` folder.

Step 1: Activate the local environment using the following command:
```powershell  
C:/Users/usman/.virtualenvs/PushshiftDumps_repo-24F2NPBl/Scripts/Activate.ps1
```

Acitvate the local env: C:/Users/usman/.virtualenvs/PushshiftDumps_repo-24F2NPBl/Scripts/Activate.ps1


Then replace the file name in the filter_file.py script with the name of the file you want to filter.

Then run the script using the command:

```
python .\scripts\filter_file.py
```