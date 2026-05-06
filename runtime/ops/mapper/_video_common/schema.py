# -*- coding: utf-8 -*-
def init_tracks_schema(video_path, fps, width, height):
    return {
        "video": video_path,
        "fps": float(fps),
        "width": int(width),
        "height": int(height),
        "frames": []  # {"frame_id": i, "objects":[{"track_id":..,"bbox":[..],...}]}
    }