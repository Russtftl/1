// Элементы DOM
const generateBtn = document.getElementById('generateBtn');
const refineBtn = document.getElementById('refineBtn');
const newLogoBtn = document.getElementById('newLogoBtn');
const companyName = document.getElementById('companyName');
const styleSelect = document.getElementById('styleSelect');
const customPrompt = document.getElementById('customPrompt');
const refinementPrompt = document.getElementById('refinementPrompt');
const generatorSection = document.getElementById('generatorSection');
const resultSection = document.getElementById('resultSection');
const resultImage = document.getElementById('resultImage');
const usedPrompt = document.getElementById('usedPrompt');
const errorMessage = document.getElementById('errorMessage');

let currentPrompt = '';
let currentSeed = null;  // Сохраняем seed для доработки

// Показать ошибку
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

// Показать загрузку
function setLoading(button, isLoading) {
    const btnText = button.querySelector('.btn-text');
    const loader = button.querySelector('.loader');

    if (isLoading) {
        btnText.style.display = 'none';
        loader.style.display = 'block';
        button.disabled = true;
    } else {
        btnText.style.display = 'inline';
        loader.style.display = 'none';
        button.disabled = false;
    }
}

// Генерация логотипа
generateBtn.addEventListener('click', async () => {
    const name = companyName.value.trim();

    if (!name) {
        showError('Пожалуйста, введите название компании');
        return;
    }

    setLoading(generateBtn, true);
    errorMessage.style.display = 'none';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_name: name,
                style: styleSelect.value,
                custom_prompt: customPrompt.value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ошибка генерации');
        }

        // Показываем результат
        currentPrompt = data.prompt;
        currentSeed = data.seed;  // Сохраняем seed
        resultImage.src = `data:image/png;base64,${data.image}`;
        usedPrompt.textContent = data.prompt;

        generatorSection.style.display = 'none';
        resultSection.style.display = 'block';

    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(generateBtn, false);
    }
});

// Доработка логотипа
refineBtn.addEventListener('click', async () => {
    const refinement = refinementPrompt.value.trim();

    if (!refinement) {
        showError('Пожалуйста, опишите что нужно изменить');
        return;
    }

    setLoading(refineBtn, true);
    errorMessage.style.display = 'none';

    try {
        const response = await fetch('/refine', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                original_prompt: currentPrompt,
                refinement: refinement,
                seed: currentSeed  // Передаем seed для сохранения структуры
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ошибка доработки');
        }

        // Обновляем результат
        currentPrompt = data.prompt;
        currentSeed = data.seed;  // Обновляем seed
        resultImage.src = `data:image/png;base64,${data.image}`;
        usedPrompt.textContent = data.prompt;
        refinementPrompt.value = '';

        // Плавная прокрутка к изображению
        resultImage.scrollIntoView({ behavior: 'smooth', block: 'center' });

    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(refineBtn, false);
    }
});

// Создать новый логотип
newLogoBtn.addEventListener('click', () => {
    resultSection.style.display = 'none';
    generatorSection.style.display = 'block';
    refinementPrompt.value = '';
    currentPrompt = '';
    currentSeed = null;  // Сбрасываем seed

    // Плавная прокрутка наверх
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Enter для отправки (Ctrl+Enter в textarea)
companyName.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        generateBtn.click();
    }
});

customPrompt.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        generateBtn.click();
    }
});

refinementPrompt.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        refineBtn.click();
    }
});
