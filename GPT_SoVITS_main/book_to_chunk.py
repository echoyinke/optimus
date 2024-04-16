import os
import json
import uuid
def clean_text_lines(file_lines):
    cleaned_lines = []
    filter_list = ['分界线', 
                '声明：',
                '本章完',
                '用户上传',
                '写在前面：']
    for line in file_lines:
        # clean the start and end 
        line = line.strip("- \n\t")
        for filter_str in filter_list:
            if filter_str in line:
                line = ''
        if len(line) >= 2 and line[0] == '（' and line[-1] == '）':
            line = ''
        if line:
            cleaned_lines.append(line)
    return cleaned_lines

def split_book_into_chunk(file_path, chunk_size=500, output_dir='../chunks_outputs', sep='\n'):
    with open(file_path, 'r') as f:
        file_lines = f.readlines()
    # clean text
    cleaned_lines = clean_text_lines(file_lines)
    # split book into chunks
    content = []
    for line in cleaned_lines:
        if '第' in line and '章' in line and '。'not in line:
            content.append({"chapter_name": line, "chunks": []})
        else:
            if content:
                latest_chunk = content[-1]["chunks"]

                if not latest_chunk:
                    latest_chunk.append(line)  
                else:
                    cur_size = len(latest_chunk[-1])
                    if cur_size < chunk_size and \
                        chunk_size - cur_size > cur_size + len(line) - chunk_size:
                        if cur_size:
                            line = sep + line
                        latest_chunk[-1] += line
                    else:
                        latest_chunk.append(line)

    file_name = file_path.split('/')[-1].replace('.txt', '')
    book_dir = os.path.join(output_dir, file_name)
    os.makedirs(book_dir, exist_ok=True)

    # save chunks
    for i, chapter in enumerate(content):
        chapter_dir = os.path.join(book_dir, f"chapter_{i}")
        os.makedirs(chapter_dir, exist_ok=True)
        for j, text in enumerate(chapter["chunks"]):
            chunk_json = {
                "book_name" : file_name,
                # 对book_name赋予一个随机的uuid
                "book_id" : str(uuid.uuid1()), 
                "chapter_name" : chapter["chapter_name"],
                "chapter_index" : i,
                "chunk_index" : j,
                "chunk_size" : len(text),
                "chunk_text" : text
            }
            json.dump(chunk_json, open(os.path.join(chapter_dir, f"chunk_{j}.json"), 'w'), ensure_ascii=False, indent=4)

    return content
    
if __name__ == '__main__':
    file_path = '../novel_material/天下第一掌柜.txt'
    output_dir = '../chunks_outputs'
    split_book_into_chunk(file_path, chunk_size=500, output_dir=output_dir)

    
