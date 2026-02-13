const crypto = require('crypto');

/**
 * Verify Telegram Web App authentication data
 * @param {string} initData - Telegram initData from WebApp
 * @param {string} botToken - Telegram bot token
 * @returns {object|null} - User data if valid, null if invalid
 */
function verifyTelegramAuth(initData, botToken) {
  try {
    // Parse initData
    const urlParams = new URLSearchParams(initData);
    const hash = urlParams.get('hash');

    if (!hash) {
      console.error('No hash found in initData');
      return null;
    }

    // Remove hash from data for verification
    urlParams.delete('hash');
    const dataToCheck = Array.from(urlParams.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');

    // Create secret key from bot token
    const secretKey = crypto.createHash('sha256')
      .update(botToken)
      .digest();

    // Calculate expected hash
    const expectedHash = crypto.createHmac('sha256', secretKey)
      .update(dataToCheck)
      .digest('hex');

    if (expectedHash !== hash) {
      console.error('Hash verification failed');
      return null;
    }

    // Parse user data
    const userString = urlParams.get('user');
    if (!userString) {
      console.error('No user data found');
      return null;
    }

    const user = JSON.parse(userString);

    // Check if auth data is not too old (within 24 hours)
    const authDate = parseInt(urlParams.get('auth_date'));
    const now = Math.floor(Date.now() / 1000);
    const timeDiff = now - authDate;

    if (timeDiff > 86400) { // 24 hours in seconds
      console.error('Auth data is too old');
      return null;
    }

    return {
      id: user.id,
      first_name: user.first_name,
      last_name: user.last_name || '',
      username: user.username,
      language_code: user.language_code,
      is_premium: user.is_premium || false,
      auth_date: authDate
    };

  } catch (error) {
    console.error('Error verifying Telegram auth:', error);
    return null;
  }
}

/**
 * Generate JWT token for internal use
 * @param {object} user - User data
 * @returns {string} - JWT token
 */
function generateJWT(user) {
  const payload = {
    telegram_id: user.id,
    name: `${user.first_name} ${user.last_name || ''}`.trim(),
    username: user.username,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60) // 24 hours
  };

  // Simple JWT implementation (in production, use proper JWT library)
  const header = Buffer.from(JSON.stringify({
    alg: 'HS256',
    typ: 'JWT'
  })).toString('base64url');

  const encodedPayload = Buffer.from(JSON.stringify(payload)).toString('base64url');

  const secret = process.env.JWT_SECRET || 'your-jwt-secret-key';
  const signature = crypto.createHmac('sha256', secret)
    .update(`${header}.${encodedPayload}`)
    .digest('base64url');

  return `${header}.${encodedPayload}.${signature}`;
}

/**
 * Verify JWT token
 * @param {string} token - JWT token
 * @returns {object|null} - Decoded payload or null if invalid
 */
function verifyJWT(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const [header, payload, signature] = parts;

    const secret = process.env.JWT_SECRET || 'your-jwt-secret-key';
    const expectedSignature = crypto.createHmac('sha256', secret)
      .update(`${header}.${payload}`)
      .digest('base64url');

    if (signature !== expectedSignature) return null;

    const decodedPayload = JSON.parse(Buffer.from(payload, 'base64url').toString());

    // Check expiration
    if (decodedPayload.exp && decodedPayload.exp < Math.floor(Date.now() / 1000)) {
      return null;
    }

    return decodedPayload;

  } catch (error) {
    console.error('JWT verification error:', error);
    return null;
  }
}

/**
 * Middleware to verify JWT token
 */
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    return res.status(401).json({
      success: false,
      message: 'Access token required'
    });
  }

  const user = verifyJWT(token);
  if (!user) {
    return res.status(403).json({
      success: false,
      message: 'Invalid or expired token'
    });
  }

  req.user = user;
  next();
}

/**
 * Create session for user
 * @param {number} telegramId - Telegram user ID
 * @returns {string} - Session token
 */
function createSession(telegramId) {
  const sessionToken = crypto.randomBytes(32).toString('hex');
  const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 hours

  return {
    telegram_id: telegramId,
    session_token: sessionToken,
    expires_at: expiresAt
  };
}

module.exports = {
  verifyTelegramAuth,
  generateJWT,
  verifyJWT,
  authenticateToken,
  createSession
};