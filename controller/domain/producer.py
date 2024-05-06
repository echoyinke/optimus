# main_program.py
import logging
import os
import json
import controller.database.db_operations as db
from GPT_SoVITS_main.book_to_chunk import split_book_into_chunk
from GPT_SoVITS_main.chunk_to_speech import chunk_to_speech


# 0. 把小说兵临城下放到文件夹binglinchengxia
# 1. noval 2 chapter chunk
novel_file_path="D:/temp_medias/binglinchengxia/兵临城下.txt"
chunk_output_dir="D:/temp_medias/binglinchengxia/"


def buildData(processed_data, file_type, status):
    dataDO = []
    import datetime
    now = datetime.datetime.now()
    dataDO['createTime'] = now
    dataDO['updateTime'] = now
    # 假设bizDate也是当前日期
    dataDO['bizDate'] = now.date()
    # dataDO['name'] = now.date()
    dataDO['type'] = file_type
    dataDO['hashTag'] = processed_data
    dataDO['status'] = status


def process_file_and_store(file_path, file_type):
    # 连接到数据库
    conn = db.connect_to_db()

    chunk_json_path_list = split_book_into_chunk(file_path=novel_file_path, output_dir=chunk_output_dir)

    try:
        for chunk_path in chunk_json_path_list:
            chunk_json = json.load(open(chunk_path, 'r', encoding='utf-8'))
            directory_path = os.path.dirname(chunk_path)
            file_name_with_extension = os.path.basename(chunk_path)
            # 使用os.path.splitext去除文件扩展名，留下 'chunk_1'
            file_name = os.path.splitext(file_name_with_extension)[0]
            output_path = os.path.join(directory_path, file_name)
            ref_wav_path = 'D:/PyProj\optimus/ref_wav/疑问—哇，这个，还有这个…只是和史莱姆打了一场，就有这么多结论吗？.wav'

            # insert chunk path to READY
            dataDO = buildData(chunk_path, file_type, 'READY');

            # 将处理后的数据插入到aigcFileList表中
            id = db.insert_into_aigcFileList(conn, dataDO)
            logging.info(f"File processed and stored successfully with data: {chunk_path}")

            chunk_to_speech(chunk_path, ref_wav_path, output_path, max_iter=600)

            # todo chunk_to_speech 返回处理结果
            processing_result = []
            if not processing_result['success']:
                logging.error("File processing failed.")
                return
            # update status  to FINISH
            db.updateStatus(conn, id, 'FINISH')
            logging.info(f"File processed and stored successfully with data: {chunk_path}")
    except Exception as e:
            logging.error(f"Error storing data to database: {e}")
    finally:
        # 关闭数据库连接
        conn.close()





