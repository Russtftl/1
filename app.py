from flask import Flask, render_template, request, jsonify
import requests
import base64
import time
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# API ключ Yandex Cloud
API_KEY = os.getenv('YANDEX_API_KEY', 'YOUR_API_KEY_HERE')

# Заготовленные стили для логотипов
PRESET_STYLES = {
    'minimalist': 'минималистичный логотип, чистый дизайн, простые геометрические формы',
    'modern': 'современный логотип, яркие цвета, динамичный дизайн',
    'geometric': 'геометрический логотип, четкие линии, абстрактные формы',
    'vintage': 'винтажный логотип, ретро стиль, классические элементы',
    'tech': 'технологичный логотип, футуристичный стиль, цифровой дизайн',
    'corporate': 'корпоративный логотип, профессиональный вид, строгий стиль',
    'creative': 'креативный логотип, художественный стиль, яркие цвета',
    'elegant': 'элегантный логотип, изысканный дизайн, утонченные формы'
}


def generate_image(prompt, seed=None, model='yandex-art'):
    """Генерация изображения через Yandex Art API

    Args:
        prompt: текст промпта
        seed: seed для воспроизводимости (если None - генерируется новый)
        model: модель для генерации
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}"
    }

    # Генерируем или используем существующий seed
    if seed is None:
        seed = int(time.time())

    # Формируем запрос на генерацию
    payload = {
        "modelUri": f"art://{os.getenv('FOLDER_ID', 'b1g...')}/yandex-art/latest",
        "generationOptions": {
            "seed": seed,
            "aspectRatio": {
                "widthRatio": "1",
                "heightRatio": "1"
            }
        },
        "messages": [
            {
                "weight": "1",
                "text": prompt
            }
        ]
    }

    try:
        # Создаем асинхронную операцию генерации
        create_response = requests.post(
            'https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync',
            headers=headers,
            json=payload,
            timeout=30
        )

        if create_response.status_code != 200:
            return {'error': f'Ошибка создания запроса: {create_response.text}'}

        operation_id = create_response.json().get('id')

        if not operation_id:
            return {'error': 'Не получен ID операции'}

        # Проверяем статус операции
        max_attempts = 60  # Максимум 60 попыток (около 2 минут)
        attempt = 0

        while attempt < max_attempts:
            time.sleep(2)  # Ждем 2 секунды между проверками

            status_response = requests.get(
                f'https://llm.api.cloud.yandex.net:443/operations/{operation_id}',
                headers=headers,
                timeout=30
            )

            if status_response.status_code != 200:
                return {'error': f'Ошибка проверки статуса: {status_response.text}'}

            result = status_response.json()

            if result.get('done'):
                if 'error' in result:
                    return {'error': f"Ошибка генерации: {result['error']}"}

                # Получаем base64 изображение
                image_base64 = result.get('response', {}).get('image')

                if image_base64:
                    return {'success': True, 'image': image_base64, 'seed': seed}
                else:
                    return {'error': 'Изображение не найдено в ответе'}

            attempt += 1

        return {'error': 'Превышено время ожидания генерации'}

    except requests.exceptions.Timeout:
        return {'error': 'Превышено время ожидания запроса'}
    except Exception as e:
        return {'error': f'Ошибка: {str(e)}'}


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html', styles=PRESET_STYLES)


@app.route('/generate', methods=['POST'])
def generate():
    """Обработка запроса на генерацию логотипа"""
    data = request.json

    company_name = data.get('company_name', '').strip()
    custom_prompt = data.get('custom_prompt', '').strip()
    style = data.get('style', '')

    if not company_name:
        return jsonify({'error': 'Введите название фирмы'}), 400

    # Формируем финальный промпт
    base_prompt = f'Создай логотип для компании "{company_name}".'

    if style and style in PRESET_STYLES:
        base_prompt += f' {PRESET_STYLES[style]}.'

    if custom_prompt:
        base_prompt += f' {custom_prompt}.'

    # base_prompt += ' Логотип должен быть на прозрачном или белом фоне, профессиональный вид.'

    # Генерируем изображение
    result = generate_image(base_prompt)

    if 'error' in result:
        return jsonify(result), 500

    return jsonify({
        'success': True,
        'image': result['image'],
        'prompt': base_prompt,
        'seed': result['seed']
    })


@app.route('/refine', methods=['POST'])
def refine():
    """Доработка существующего логотипа с сохранением базовой структуры"""
    data = request.json

    original_prompt = data.get('original_prompt', '').strip()
    refinement = data.get('refinement', '').strip()
    original_seed = data.get('seed')  # Получаем оригинальный seed

    if not original_prompt or not refinement:
        return jsonify({'error': 'Необходимы оригинальный промпт и дополнение'}), 400

    # Объединяем промпты для дополнения
    new_prompt = f'{original_prompt} Дополнительно: {refinement}'

    # Генерируем изображение с тем же seed для сохранения структуры
    result = generate_image(new_prompt, seed=original_seed)

    if 'error' in result:
        return jsonify(result), 500

    return jsonify({
        'success': True,
        'image': result['image'],
        'prompt': new_prompt,
        'seed': result['seed']
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
