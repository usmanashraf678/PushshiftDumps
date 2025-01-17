import sys
import requests
import time
import discord_logging
import argparse
import os
import re
import zstandard
from datetime import datetime, timedelta
import json
import praw
from praw import endpoints
import prawcore
import logging.handlers

sys.path.append('personal')

log = discord_logging.init_logging(debug=False)

import utils
import classes
from classes import IngestType
from merge import ObjectType


NEWLINE_ENCODED = "\n".encode('utf-8')
reg = re.compile(r"\d\d-\d\d-\d\d_\d\d-\d\d")


def end_of_day(input_minute):
	return input_minute.replace(hour=0, minute=0, second=0) + timedelta(days=1)


def build_day(day_to_process, input_folders, output_folder, object_type, reddit):
	log.info(f"Using pushshift token: {pushshift_token}")

	file_type = "comments" if object_type == ObjectType.COMMENT else "submissions"

	file_minutes = {}
	minute_iterator = day_to_process - timedelta(minutes=2)
	end_time = end_of_day(day_to_process) + timedelta(minutes=2)
	while minute_iterator <= end_time:
		file_minutes[minute_iterator] = []
		minute_iterator += timedelta(minutes=1)

	for merge_folder, ingest_type in input_folders:
		merge_date_folder = os.path.join(merge_folder, file_type, day_to_process.strftime('%y-%m-%d'))
		if os.path.exists(merge_date_folder):
			for file in os.listdir(merge_date_folder):
				match = reg.search(file)
				if not match:
					log.info(f"File doesn't match regex: {file}")
					continue
				file_date = datetime.strptime(match.group(), '%y-%m-%d_%H-%M')
				if file_date in file_minutes:
					file_minutes[file_date].append((os.path.join(merge_date_folder, file), ingest_type))

	objects = classes.ObjectDict(day_to_process, day_to_process + timedelta(days=1) - timedelta(seconds=1), object_type)
	unmatched_field = False
	minute_iterator = day_to_process - timedelta(minutes=2)
	working_lowest_minute = day_to_process
	last_minute_of_day = end_of_day(day_to_process) - timedelta(minutes=1)
	while minute_iterator <= end_time:
		for ingest_file, ingest_type in file_minutes[minute_iterator]:
			for obj in utils.read_obj_zst(ingest_file):
				if objects.add_object(obj, ingest_type):
					unmatched_field = True
		log.info(f"Loaded {minute_iterator.strftime('%y-%m-%d_%H-%M')} : {objects.get_counts_string_by_minute(minute_iterator, [IngestType.INGEST, IngestType.RESCAN, IngestType.DOWNLOAD])}")

		if minute_iterator >= end_time or objects.count_minutes() >= 11:
			if minute_iterator > last_minute_of_day:
				working_highest_minute = last_minute_of_day
			else:
				working_highest_minute = minute_iterator - timedelta(minutes=1)
			missing_ids, start_id, end_id = objects.get_missing_ids_by_minutes(working_lowest_minute, working_highest_minute)
			log.debug(
				f"Backfilling from: {working_lowest_minute.strftime('%y-%m-%d_%H-%M')} ({utils.base36encode(start_id)}|{start_id}) to "
				f"{working_highest_minute.strftime('%y-%m-%d_%H-%M')} ({utils.base36encode(end_id)}|{end_id}) with {len(missing_ids)} ({end_id - start_id}) ids")

			for chunk in utils.chunk_list(missing_ids, 50):
				pushshift_objects, pushshift_token = query_pushshift(chunk, pushshift_token, object_type)
				for pushshift_object in pushshift_objects:
					if objects.add_object(pushshift_object, IngestType.PUSHSHIFT):
						unmatched_field = True

			for chunk in utils.chunk_list(missing_ids, 100):
				reddit_objects = query_reddit(chunk, reddit, object_type)
				for reddit_object in reddit_objects:
					if objects.add_object(reddit_object['data'], IngestType.BACKFILL):
						unmatched_field = True

			for missing_id in missing_ids:
				if missing_id not in objects.by_id:
					objects.add_missing_object(missing_id)

			objects.delete_objects_below_minute(working_lowest_minute)
			while working_lowest_minute <= working_highest_minute:
				folder = os.path.join(output_folder, file_type, working_lowest_minute.strftime('%y-%m-%d'))
				if not os.path.exists(folder):
					os.makedirs(folder)
				output_path = os.path.join(folder, f"{('RS' if object_type == ObjectType.COMMENT else 'RC')}_{working_lowest_minute.strftime('%y-%m-%d_%H-%M')}.zst")
				output_handle = zstandard.ZstdCompressor().stream_writer(open(output_path, 'wb'))

				for obj in objects.by_minute[working_lowest_minute].obj_list:
					output_handle.write(json.dumps(obj, sort_keys=True).encode('utf-8'))
					output_handle.write(NEWLINE_ENCODED)
					objects.delete_object_id(obj['id'])
				log.info(
					f"Wrote up to {working_lowest_minute.strftime('%y-%m-%d_%H-%M')} : "
					f"{objects.get_counts_string_by_minute(working_lowest_minute, [IngestType.PUSHSHIFT, IngestType.BACKFILL, IngestType.MISSING])}")
				output_handle.close()
				working_lowest_minute += timedelta(minutes=1)

			objects.rebuild_minute_dict()

		discord_logging.flush_discord()
		if unmatched_field:
			log.warning(f"Unmatched field, aborting")
			discord_logging.flush_discord()
			sys.exit(1)

		minute_iterator += timedelta(minutes=1)

	log.info(f"Finished day {day_to_process.strftime('%y-%m-%d')}: {objects.get_counts_string()}")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Combine the minute files into a single month")
	parser.add_argument("--type", help="The object type, either comments or submissions", required=True)
	parser.add_argument("--month", help="The month to process, format YY-MM", required=True)
	parser.add_argument('--input', help='Input folder', required=True)
	parser.add_argument('--output', help='Output folder', required=True)
	parser.add_argument("--debug", help="Enable debug logging", action='store_const', const=True, default=False)
	parser.add_argument("--level", help="The compression ratio to output at", default="3")
	args = parser.parse_args()

	if args.debug:
		discord_logging.set_level(logging.DEBUG)

	month = datetime.strptime(args.month, '%y-%m')
	level = int(args.level)

	log.info(f"Input folder: {args.input}")
	log.info(f"Output folder: {args.output}")
	log.info(f"Month: {args.month}")
	log.info(f"Compression level: {level}")

	prefix = None
	if args.type == "comments":
		prefix = "RC"
	elif args.type == "submissions":
		prefix = "RS"
	else:
		log.error(f"Invalid type: {args.type}")
		sys.exit(2)

	output_path = os.path.join(args.output, args.type, f"{prefix}_{month.strftime('%Y-%m')}.zst")
	output_handle = zstandard.ZstdCompressor(level=level).stream_writer(open(output_path, 'wb'))

	count_objects = 0
	minute_iterator = month
	end_time = month.replace(month=month.month + 1)
	while minute_iterator < end_time:
		minute_file_path = os.path.join(args.input, args.type, minute_iterator.strftime('%y-%m-%d'), f"{prefix}_{minute_iterator.strftime('%y-%m-%d_%H-%M')}.zst")
		for obj, line, _ in utils.read_obj_zst_meta(minute_file_path):
			output_handle.write(line.encode('utf-8'))
			output_handle.write(NEWLINE_ENCODED)

			count_objects += 1
			if count_objects % 100000 == 0:
				log.info(f"{minute_iterator.strftime('%y-%m-%d_%H-%M')} : {count_objects:,}")

		minute_iterator += timedelta(minutes=1)

	log.info(f"{minute_iterator.strftime('%y-%m-%d_%H-%M')} : {count_objects:,}")
	output_handle.close()
