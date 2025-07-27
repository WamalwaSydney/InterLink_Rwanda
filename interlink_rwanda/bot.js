// whatsappBot.js

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const bodyParser = require('body-parser');

const app = express();
app.use(bodyParser.json());

const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './.wwebjs_auth' }),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        headless: true
    }
});

let isClientReady = false;

// Show QR when needed
client.on('qr', (qr) => {
    console.log('📱 Scan this QR Code to log in:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('✅ WhatsApp client is ready');
    isClientReady = true;
});

client.on('auth_failure', (msg) => {
    console.error('❌ Authentication failed:', msg);
});

client.on('disconnected', (reason) => {
    console.warn('⚠️ WhatsApp client was disconnected:', reason);
    isClientReady = false;
});

// Optional: Log incoming messages (for debugging)
client.on('message', msg => {
    console.log(`📥 Message from ${msg.from}: ${msg.body}`);
});

async function sendJobToGroup(groupName, job) {
    const chats = await client.getChats();
    const group = chats.find(chat => chat.isGroup && chat.name === groupName);

    if (!group) {
        throw new Error(`Group "${groupName}" not found. Ensure the bot is a member.`);
    }

    const message = `📢 *New Job Alert!*\n\n` +
                    `*Title:* ${job.title}\n` +
                    `*Company:* ${job.company}\n` +
                    `*Location:* ${job.location || 'N/A'}\n` +
                    `*Skills:* ${job.skills || 'N/A'}\n\n` +
                    `🔗 Apply: ${job.url || 'No URL provided'}`;

    await client.sendMessage(group.id._serialized, message);
}

// API Endpoint
app.post('/send-job', async (req, res) => {
    if (!isClientReady) {
        return res.status(503).json({ error: 'WhatsApp client not ready yet. Try again shortly.' });
    }

    const job = req.body;

    if (!job.title || !job.company) {
        return res.status(400).json({ error: 'Missing required job fields: title, company' });
    }

    try {
        await sendJobToGroup('InterLink Rwanda Jobs', job); // <- Replace with your group name
        res.json({ status: 'Job sent successfully to WhatsApp' });
    } catch (e) {
        console.error('❌ Error:', e.message);
        res.status(500).json({ error: e.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🌐 HTTP API listening at http://localhost:${PORT}`);
});

client.initialize();
