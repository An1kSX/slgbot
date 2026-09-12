function addMessage({id, sender, text, time, avatarUrl, replyTo = 'None'}) {
    const chatBody = document.querySelector('.chat-body');
    
    // Создаем основной контейнер сообщения
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.setAttribute('data-id', id);
    messageDiv.setAttribute('data-reply-to', replyTo);

    // Создаем элемент для аватарки
    const avatarImg = document.createElement('img');
    avatarImg.classList.add('avatar');
    avatarImg.src = avatarUrl;
    avatarImg.alt = 'Avatar';

    // Создаем контейнер для контента сообщения
    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');

    // Если сообщение является ответом, добавляем цитату
    if (replyTo !== 'None') {
        const replyDiv = document.createElement('div');
        replyDiv.classList.add('reply-to');
        
        // Найдите исходное сообщение по его ID
        const originalMessage = document.querySelector(`.message[data-id="${replyTo}"]`);
        if (originalMessage) {
            const originalSender = originalMessage.querySelector('.sender').textContent;
            const originalText = originalMessage.querySelector('.text').textContent;
            
            // Создаем элемент для отображения цитаты
            const replySenderDiv = document.createElement('div');
            replySenderDiv.classList.add('reply-sender');
            replySenderDiv.textContent = originalSender;
            
            const replyTextDiv = document.createElement('div');
            replyTextDiv.classList.add('reply-text');
            replyTextDiv.textContent = originalText;
            
            replyDiv.appendChild(replySenderDiv);
            replyDiv.appendChild(replyTextDiv);
            messageContent.appendChild(replyDiv);
        }
    }

    // Создаем элемент для имени отправителя
    const senderDiv = document.createElement('div');
    senderDiv.classList.add('sender');
    senderDiv.textContent = sender;

    // Создаем элемент для текста сообщения
    const textDiv = document.createElement('div');
    textDiv.classList.add('text');
    textDiv.textContent = text;

    // Создаем элемент для времени отправки сообщения
    const timeDiv = document.createElement('div');
    timeDiv.classList.add('time');
    timeDiv.textContent = time;

    // Добавляем элементы в контейнер сообщения
    messageContent.appendChild(senderDiv);
    messageContent.appendChild(textDiv);
    messageContent.appendChild(timeDiv);

    messageDiv.appendChild(avatarImg);
    messageDiv.appendChild(messageContent);

    // Добавляем сообщение в тело чата
    chatBody.appendChild(messageDiv);
}

function addImageMessage({id, sender, avatarUrl, imageUrl, time, caption = null, replyTo = null}) {
    const chatBody = document.querySelector('.chat-body');

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.setAttribute('data-id', id);
    if (replyTo) {
        messageDiv.classList.add('reply'); // Добавляем класс для стилей ответа
    }

    const avatarImg = document.createElement('img');
    avatarImg.classList.add('avatar');
    avatarImg.src = avatarUrl;
    avatarImg.alt = 'Avatar';

    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');

    const senderDiv = document.createElement('div');
    senderDiv.classList.add('sender');
    senderDiv.textContent = sender;

    if (replyTo) {
        const replyDiv = document.createElement('div');
        replyDiv.classList.add('reply-to');

        const originalMessage = document.querySelector(`.message[data-id="${replyTo}"]`);
        if (originalMessage) {
            const originalSender = originalMessage.querySelector('.sender').textContent;
            const originalText = originalMessage.querySelector('.text') ? originalMessage.querySelector('.text').textContent : "Reply to an image";

            const replySenderDiv = document.createElement('div');
            replySenderDiv.classList.add('reply-sender');
            replySenderDiv.textContent = originalSender;

            const replyTextDiv = document.createElement('div');
            replyTextDiv.classList.add('reply-text');
            replyTextDiv.textContent = originalText;

            replyDiv.appendChild(replySenderDiv);
            replyDiv.appendChild(replyTextDiv);
            messageContent.appendChild(replyDiv);
        }
    }

    const imageElem = document.createElement('img');
    imageElem.classList.add('message-image');
    imageElem.src = imageUrl;
    imageElem.alt = 'Image';

    messageContent.appendChild(senderDiv);
    messageContent.appendChild(imageElem);

    // Добавляем caption под картинкой как обычный текст
    if (caption) {
        const captionDiv = document.createElement('div');
        captionDiv.classList.add('text');
        captionDiv.textContent = caption;
        messageContent.appendChild(captionDiv);
    }

    const timeDiv = document.createElement('div');
    timeDiv.classList.add('time');
    timeDiv.textContent = time;

    messageContent.appendChild(timeDiv);

    messageDiv.appendChild(avatarImg);
    messageDiv.appendChild(messageContent);

    chatBody.appendChild(messageDiv);
}


function addFileMessage({id, sender, avatarUrl, fileName, fileUrl, iconUrl, time, caption = null, replyTo = null}) {
    const chatBody = document.querySelector('.chat-body');

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.setAttribute('data-id', id);
    if (replyTo) {
        messageDiv.classList.add('reply'); // Добавляем класс для стилей ответа
    }

    const avatarImg = document.createElement('img');
    avatarImg.classList.add('avatar');
    avatarImg.src = avatarUrl;
    avatarImg.alt = 'Avatar';

    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');

    const senderDiv = document.createElement('div');
    senderDiv.classList.add('sender');
    senderDiv.textContent = sender;

    if (replyTo) {
        const replyDiv = document.createElement('div');
        replyDiv.classList.add('reply-to');

        const originalMessage = document.querySelector(`.message[data-id="${replyTo}"]`);
        if (originalMessage) {
            const originalSender = originalMessage.querySelector('.sender').textContent;
            const originalText = originalMessage.querySelector('.text') ? originalMessage.querySelector('.text').textContent : "Reply to a file";

            const replySenderDiv = document.createElement('div');
            replySenderDiv.classList.add('reply-sender');
            replySenderDiv.textContent = originalSender;

            const replyTextDiv = document.createElement('div');
            replyTextDiv.classList.add('reply-text');
            replyTextDiv.textContent = originalText;

            replyDiv.appendChild(replySenderDiv);
            replyDiv.appendChild(replyTextDiv);
            messageContent.appendChild(replyDiv);
        }
    }

    const fileContainer = document.createElement('div');
    fileContainer.classList.add('file-container');

    const fileIcon = document.createElement('img');
    fileIcon.classList.add('file-icon');
    fileIcon.src = iconUrl;
    fileIcon.alt = 'File Icon';

    const fileLink = document.createElement('a');
    fileLink.classList.add('file-link');
    fileLink.href = fileUrl;
    fileLink.target = '_blank';
    fileLink.textContent = fileName;

    fileContainer.appendChild(fileIcon);
    fileContainer.appendChild(fileLink);

    messageContent.appendChild(senderDiv);
    messageContent.appendChild(fileContainer);

    // Добавляем caption под файлом как обычный текст
    if (caption) {
        const captionDiv = document.createElement('div');
        captionDiv.classList.add('text');
        captionDiv.textContent = caption;
        messageContent.appendChild(captionDiv);
    }

    const timeDiv = document.createElement('div');
    timeDiv.classList.add('time');
    timeDiv.textContent = time;

    messageContent.appendChild(timeDiv);

    messageDiv.appendChild(avatarImg);
    messageDiv.appendChild(messageContent);

    chatBody.appendChild(messageDiv);
}

