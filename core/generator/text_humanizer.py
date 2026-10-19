import random
import re


class TextHumanizer:
    """Mengubah teks hasil AI menjadi teks yang memiliki ritme, burstiness, dan diksi alami manusia."""

    def __init__(self):
        # Daftar kata AI yang harus dihindari (banned words)
        self.ai_words = {
            "delve": "mendalami",
            "crucial": "mendasar",
            "krusial": "mendasar",
            "furthermore": "lebih lanjut",
            "moreover": "di samping itu",
            "in conclusion": "sebagai penutup",
            "it is important to note": "perlu dicatat",
            "tapestry": "anyaman",
            "menyelami": "menelaah",
            "sangat penting untuk dicatat": "perlu digarisbawahi",
            "sebagai kesimpulan": "pada akhirnya",
        }

        # Transisi manusiawi
        self.human_transitions = [
            "Anehnya, ", "Pada praktiknya, ", "Meskipun demikian, ",
            "Kenyataannya, ", "Tentu saja, ", "Sayangnya, ",
            "Di sisi lain, ", "Menariknya, "
        ]

    def humanize(self, text: str) -> str:
        if not text or not text.strip():
            return text

        # 1. Ganti kata-kata khas AI
        for ai_word, replacement in self.ai_words.items():
            text = re.sub(rf'\b{re.escape(ai_word)}\b', replacement, text, flags=re.IGNORECASE)

        # 2. Pecah teks menjadi kalimat
        sentences = re.split(r'(?<=[.!?])\s+', text)
        humanized_sentences = []

        for i, sentence in enumerate(sentences):
            s_clean = sentence.strip()
            if not s_clean:
                continue

            # 3. Burstiness: Acak panjang kalimat
            # Jika kalimat terlalu panjang (> 25 kata), potong jadi dua
            words = s_clean.split()
            if len(words) > 25 and random.random() > 0.45:
                mid = len(words) // 2
                part1 = " ".join(words[:mid])
                if not part1.endswith(('.', '!', '?')):
                    part1 += "."
                part2 = " ".join(words[mid:])
                if part2:
                    part2 = part2[0].upper() + part2[1:]
                    humanized_sentences.append(part1)
                    humanized_sentences.append(part2)
                else:
                    humanized_sentences.append(part1)
            else:
                humanized_sentences.append(s_clean)

            # 4. Sisipkan transisi manusiawi secara acak setiap 3 kalimat
            if i > 0 and i % 3 == 0 and random.random() > 0.6:
                transition = random.choice(self.human_transitions)
                target = humanized_sentences[-1]
                if target and not any(target.startswith(t) for t in self.human_transitions):
                    humanized_sentences[-1] = transition + target[0].lower() + target[1:]

        # 5. Gabungkan kembali dengan spasi yang alami
        final_text = ""
        for s in humanized_sentences:
            final_text += s + " "
            if random.random() > 0.92:
                final_text += " "  # Tambah variasi spasi alami manusia

        return final_text.strip()
