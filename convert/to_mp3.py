import pika, json, os, tempfile
from bson.objectid import ObjectId
import pika.spec
import moviepy

def start(message, fs_videos, fs_mp3s, channel):
    message = json.loads(message)

    #empty temp file
    tf = tempfile.NamedTemporaryFile()
    
    #video content
    out = fs_videos.get(ObjectId(message['video_fid']))

    #add video content to empty file
    tf.write(out.read())

    #create audio from temp video file
    audio = moviepy.editor.VideoFileClip(tf.name).audio

    tf.close()

    # write the audio to the file
    tf_path = tempfile.gettempdir() + '/' + message['video_fid'] + '.mp3'

    audio.write_audiofile(tf_path)

    #save to file to mongo
    f = open(tf_path, 'rb')
    data = f.read()
    fid = fs_mp3s.put(data)
    f.close()

    os.remove(tf_path)

    message['mp3_fid'] = str(fid)

    try:
        channel.basic_publish(
            exchange='',
            routing_key=os.environ.get('MP3_QUEUE', 'mp3_queue'),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,  # make message persistent
            ),
        )
    except Exception as e:
        fs_mp3s.delete(fid)
        return "failed to publish message: "
    