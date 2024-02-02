# Overview

This repo has been adapted from the original [Pushshift Dumps repo](https://github.com/Watchful1/PushshiftDumps) to extract IDs of all posts made in a subreddit from the beginning of its creation. This repo relies on the Push Shifts Dumps available via academic torrents [here](https://academictorrents.com/details/c398a571976c78d346c325bd75c47b82edf6124e). This torrent has aggregated top 20k subreddits (by comments and posts) as separate zst files. Using this repo, any subreddit can be processed (using its zst file) to get the IDs of all posts made in that subreddit.

## How to download the relevant subreddit zst file?

1. In order to download the zst files, you would need to use a torrent client. I used qBittorrent for this. You can download qBittorrent [here](https://www.qbittorrent.org/download).
2. Once you have that installed, go to the torrent link and click download, this will download a small ".torrent" file.
3. In qBittorrent, click the plus at the top and select this torrent file. This will open the list of all the subreddits. Click "Select None" to unselect everything, then use the filter box in the top right to search for the subreddit you want. Select the files you're interested in, there's a separate one for the comments and submissions of each subreddit, then click okay. The files will then be downloaded.
4. We'll only be needing the submissions file for our purpose of getting the IDs of all posts made in a subreddit. For example, `subreddits/Instagram_submissions.zst` is the file for the Instagram subreddit. The post details (e.g. timestamp, title, caption, comments etc.) can be extracted using the PRAW library. This repo merely focuses on using the the Push Shift Dumps to get the IDs which can work as a seed for the post extraction process.

## How to use this repo to extract IDs of all posts made in a subreddit?

**Step 0:** Before running the script, the input files (i.e. the zst submissions files downloaded from the torrent link) should be placed in the `zst_files` folder. The file should be named as {subreddit_name}_submissions.zst where {subreddit_name} is the name of the subreddit.

**Step 1:** Activate the local environment using the following command:
```powershell  
pipenv shell
```

**Step 1a:** The following commands can be used to check if the environment has been activated:

```powershell
# in powershell
Get-Command python | Select-Object -ExpandProperty Source
```

```cmd
REM in cmd
where python
```

This should return the path to the Python executable being used. Make sure this is poining to the python executable in the virtual environment.

**Step 2:** Install the required packages using the following command:
```powershell
pipenv install
```

**Step 3:** Set the `subreddit_name`, `from_date_str` and `to_date_str` variables at the top of the `filter_file.py ` file. The subreddit_name will be the name of the subreddit that we want to extract the IDs for. The `from_date_str` and `to_date_str` are the start and end dates for the posts that we want to extract. The format for the dates is `YYYY-MM-DD` present as a string.

The input will be expected to be present in the `zst files` folder. The file name should be as {subreddit_name}_submissions.zst. `subreddit_name` in file name should be the same as the `subreddit_name` variable indicated above.

**Step 4:** Run the script using the command:

```
python .\scripts\filter_file.py
```

**Step 5:** The output can be found in the `output` folder. The output will be a text file with the name {subreddit_name}_ids.txt. This file will contain the IDs (one in each line) of all the posts made in the subreddit from the start date to the end date.