import os
from openai import OpenAI

languages = {
    'zh': '中文',
    'en': '英语',
    'hi': '印地语',
    'es': '西班牙语',
    'fr': '法语',
    'de': '德语',
    'ru': '俄语',
    'ja': '日语',
    'pt': '葡萄牙语',
    'ar': '阿拉伯语',
    'bn': '孟加拉语',
    'id': '印度尼西亚语',
    'pa': '旁遮普语',
    'ko': '韩语',
    'vi': '越南语',
    'tr': '土耳其语',
    'it': '意大利语',
    'th': '泰语',
    'nl': '荷兰语',
    'sv': '瑞典语',
    'fi': '芬兰语',
    'el': '希腊语',
    'he': '希伯来语',
    'sw': '斯瓦希里语',
    'hu': '匈牙利语',
    'cs': '捷克语',
    'ro': '罗马尼亚语',
    'da': '丹麦语',
    'no': '挪威语',
    'sk': '斯洛伐克语',
    'sl': '斯洛文尼亚语',
}

languages2 = {
    'zh': '中文',
    'en': 'English',
    'hi': 'हिन्दी',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'ru': 'Русский',
    'ja': '日本語',
    'pt': 'Português',
    'ar': 'العربية',
    'bn': 'বাংলা',
    'id': 'Bahasa Indonesia',
    'pa': 'ਪੰਜਾਬੀ',
    'ko': '한국어',
    'vi': 'Tiếng Việt',
    'tr': 'Türkçe',
    'it': 'Italiano',
    'th': 'ภาษาไทย',
    'nl': 'Nederlands',
    'sv': 'Svenska',
    'fi': 'Suomi',
    'el': 'Ελληνικά',
    'he': 'עברית',
    'sw': 'Kiswahili',
    'hu': 'Magyar',
    'cs': 'Čeština',
    'ro': 'Română',
    'da': 'Dansk',
    'no': 'Norsk',
    'sk': 'Slovenčina',
    'sl': 'Slovenščina',
}


class gpt():
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.gptsapi.net/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "")
    )
    @classmethod
    def 翻译(cls, en,prompt,不翻译的词):
        """
        多语言翻译配置
        """
        # prompt = """<div class="bg-gray-800 p-6 rounded-lg shadow-md">
        #     <h3 class="text-2xl font-semibold mb-4 text-blue-400">Game Controls</h3>
        #     <ul class="space-y-2 text-gray-300">
        #         <li><span class="font-bold text-purple-400">Drag and Drop Characters</span><span
        #                 class="font-bold text-purple-400"></span>: Simply drag and drop characters onto the stage to add sounds
        #             and animations to your mix.
        #         </li>
        #         <li><span class="font-bold text-purple-400">Tap to Activate Sounds</span>:Tap on each character to activate
        #             their unique sound, creating a dynamic musical experience
        #         </li>
        #         <li><span class="font-bold text-purple-400">Layer Sounds</span>: Combine multiple characters to layer sounds,
        #             enhancing the richness of your track.
        #         </li>
        #         <li><span class="font-bold text-purple-400">Save and Share Your Creations</span>:Once you're satisfied with your
        #             mix, save your creation and share it with friends or on social media!
        #         </li>
        #     </ul>
        # </div>
        # <div class="bg-gray-800 p-6 rounded-lg shadow-md">
        #     <h3 class="text-2xl font-semibold mb-4 text-blue-400">Mission Objectives</h3>
        #     <ul class="space-y-2 text-gray-300">
        #         <li>Combine different sounds and animations to craft your own original music tracks.</li>
        #         <li>Layer multiple sounds to discover new musical combinations and styles.</li>
        #         <li>Save and share your music with friends, showcasing your creativity.</li>
        #         <li>Complete challenges to unlock new characters and expand your sound palette.</li>
        #     </ul>
        # </div>"""
        c = f"将我提供的内容翻译为{languages[en]}，不要有额外输出，不翻译的词有{不翻译的词}"
        print(c)
        response = cls.client.chat.completions.create(
            model="gpt-4o-mini",  # 或者使用 "gpt-3.5-turbo" 如果没有 GPT-4 访问权限
            messages=[
                {"role": "system",
                 "content": c},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            n=1,
            stop=None,
            temperature=0.7,
        )
        res = response.choices[0].message.content.strip().replace("```html", "").replace("```", "")
        print(res)
        return res


