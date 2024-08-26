import re
from collections import Counter

def split_text(text, max_length=1000):
    start = 0
    split_texts = []
    while start < len(text):
        end = start + max_length
        if end < len(text):
            while end > start and text[end] not in (' ', '\n', '\t'):
                end -= 1
        if end == start:
            end = start + max_length
        split_texts.append(text[start:end])
        start = end
    return split_texts

def count_characters(text):
    # 使用Counter统计每个字符的出现次数
    char_count = Counter(text)
    # 按照出现次数倒序排序
    sorted_char_count = sorted(char_count.items(), key=lambda item: item[1], reverse=True)
    # 打印出现频率较高的字符及其次数
    for char, count in sorted_char_count:
        if count > 100:  # 只显示频率大于100的字符
            print(f"字符: '{char}' 出现次数: {count}")
    return sorted_char_count


import re


def compact_text(text):
    # 将全角空格替换为半角空格
    text = text.replace('　', ' ')
    # 去掉多余的空格(半角)和制表符
    text = re.sub(r'[ \t]+', '', text).strip()
    return text


def split_novel_into_chunks(text, chunk_size=600):
    sentences = text.split('\n')
    n = len(sentences)

    # 动态规划表，dp[i]表示前i个句子分割后的最小偏差
    dp = [float('inf')] * (n + 1)
    dp[0] = 0

    # 保存每个位置的最佳分割点
    split_points = [-1] * (n + 1)

    for i in range(1, n + 1):
        current_length = 0
        for j in range(i, 0, -1):
            current_length += len(sentences[j - 1]) + 1  # 加1是为了换行符
            if current_length > chunk_size * 1.5:  # 如果长度超过期望chunk_size的1.5倍，停止累加
                break

            # 判断是否是对话部分，避免在对话中间进行分割
            if j > 1 and (
                    sentences[j - 1].strip().startswith(("“", "\"")) or sentences[j - 2].strip().endswith(("”", "\""))):
                continue

            # 计算偏差
            deviation = abs(current_length - chunk_size)
            # 检查是否要更新dp[i]
            if dp[i] > dp[j - 1] + deviation:
                dp[i] = dp[j - 1] + deviation
                split_points[i] = j - 1

    # 反向构建chunks
    chunks = []
    index = n
    while index > 0:
        start = split_points[index]
        chunk = "\n".join(sentences[start:index])
        chunks.append(chunk)
        index = start

    chunks.reverse()
    return chunks






if __name__ == '__main__':
    input_text="一个老旧的钨丝灯被黑色的电线悬在屋子中央，闪烁着昏暗的光芒。\n　　静谧的气氛犹如墨汁滴入清水，正在房间内晕染蔓延。\n　　房间的正中央放着一张大圆桌，看起来已经斑驳不堪，桌子中央立着一尊小小的座钟，花纹十分繁复，此刻正滴答作响。\n　　而围绕桌子一周，坐着十个衣着各异的人，他们的衣服看起来有些破旧，面庞也沾染了不少灰尘。\n　　他们有的趴在桌面上，有的仰坐在椅子上，都沉沉地睡着。\n　　在这十人的身边，静静地站着一个戴着山羊头面具、身穿黑色西服的男人。\n　　他的目光从破旧的山羊头面具里穿出，饶有兴趣地盯着十个人。\n　　桌上的座钟响了起来，分针与时针同时指向了「十二」。\n　　房间之外很遥远的地方，传来了低沉的钟声。\n　　同一时刻，围坐在圆桌旁边的十个男男女女慢慢苏醒了。\n　　他们逐渐清醒之后，先是迷惘的看了看四周，又疑惑地看了看对方。\n　　看来谁都不记得自己为何出现在此处。\n　　“早安，九位。”山羊头率先说话了，“很高兴能在此与你们见面，你们已经在我面前沉睡了十二个小时了。”\n　　眼前这个男人的装扮实在是诡异，在昏暗的灯光下吓了众人一跳。\n　　他的面具仿佛是用真正的山羊头做成的，很多毛发已经发黄变黑，打结粘在了一起。\n　　山羊面具的眼睛处挖了两个空洞，露出了他那狡黠的双眼。\n　　他的举手投足之间不仅散发着山羊身上独有的膻腥味，更有一股隐隐的腐烂气息。\n　　一个纹着花臂的男人愣了几秒，才终于发现这件事情的不合理之处，带着犹豫开口问道山羊头：“你……是谁？”\n　　“相信你们都有这个疑问，那我就跟九位介绍一下。”山羊头高兴的挥舞起双手，看起来他早就准备好答案了。\n　　一位名叫齐夏的年轻人坐在距离山羊头最远的地方，他迅速打量了一下屋内的情况，片刻之后，神色就凝重了起来。\n　　奇怪，这个房间真是太奇怪了。\n　　这里没有门，四面都是墙。\n　　换句话说，这个屋子四周、屋顶和地板都是封闭的，偏偏在屋中央放着一张桌子。\n　　既然如此，他们是怎么来到这里的？\n　　难不成是先把人送过来，而后再砌成的墙吗？\n　　齐夏又看了看四周，这里不管是地板、墙面还是天花板，统统都有横竖交错的线条，这些线条将墙体和地面分成了许多大方格。\n　　另外让齐夏在意的一点，是那个山羊头口中所说的「九位」。\n　　坐在圆桌四周的无论怎么数都是十个人，加上山羊头自己，这屋里一共有十一个人。\n　　「九位」是什么意思？\n　　他伸手摸了摸自己的口袋，不出所料，手机早就被收走了。\n　　“不必跟我们介绍了。”一个清冷的女人开口对山羊头说道，“我劝你早点停止自己的行为，我怀疑你拘禁我们已经超过了二十四个小时，构成了「非法拘禁罪」，你现在所说的每一句话都会被记录下来，会形成对你不利的证词。”\n　　她一边说着话，一边嫌弃的搓弄着手臂上的灰尘，仿佛对于被囚禁来说，她更讨厌被弄脏。\n　　清冷女人的一番话确实让众人清醒不少，无论对方是谁，居然敢一个人绑架十个人，不论如何都已经触犯法律的底线了。\n　　“等等……”一个穿着白大褂的中年男人打断了众人的思路，他缓缓的看向那个清冷女人，开口问道，“我们都刚刚才醒过来，你怎么知道我们被囚禁了「二十四个小时」？”\n　　他的语气平稳而有力，但却一针见血。\n　　清冷女人不慌不忙的指了指桌面上的座钟，回答道：“这里的钟表指向十二点，可我有晚睡的习惯，我上一次在家中看表就已经十二点了，这说明我们被囚禁了至少十二小时。”\n　　她说完之后又用手指了指四周的墙面，继续说道：“你们也该发现了，这屋子里没有门，说明这个人为了让我们进到这个屋内费了一番功夫，他说我们已经沉睡了十二个小时，如今时钟再次指向十二点，说明至少转了两圈，所以我怀疑「超过二十四个小时」，有问题吗？”\n　　白大褂听完这个回答，冷冷的看了女人一眼，目光之中依然带着怀疑。\n　　毕竟在这种环境内，这个女人过于冷静了。\n　　正常人面对这种绑架行为，会冷静的说出她这番话吗？\n　　此时一个穿着黑色T恤的健壮年轻人开口问道：“山羊头，为什么这里有十个人，你却说有九个？”\n　　山羊头沉默着，并没有立刻回答。\n　　“冚家铲，我不管这里有几个人……”花臂男人骂了一声，一撑桌子想要站起身来，却发现自己的双腿瘫软使不上力气，于是只能继续指着山羊头说，“粉肠，我劝你识相点，你可能不知道惹了我有多么严重的后果，我真的会要了你的命。”\n　　此言一出，在座的男人们的表情都渐渐严肃了起来，这个时候确实需要有一个牵头人，如果能一起将这个山羊头制服，那情况还在控制中。\n　　可是众人却发现自己的双腿不知是被人注射了什么东西一样，此时完全使不上力。\n　　于是花臂男只能用语言威胁着山羊头，大声的叫骂着。\n　　齐夏没有开口，伸手微微抚摸着下巴，他盯着桌子上的座钟，若有所思。\n　　事情似乎没有想象中的那么简单。"
    cks=split_novel_into_chunks(compact_text(input_text))
    for c in  cks:
        print(len(c))