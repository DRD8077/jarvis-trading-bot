// Mock database for demo purposes
let mockDB = {
  users: [],
  chats: [],
  payments: [],
  sessions: []
};

// User Schema (Mock)
const MockUser = {
  findOne: async (query) => {
    return mockDB.users.find(user =>
      user.telegram_id === query.telegram_id ||
      user._id === query._id
    ) || null;
  },
  find: async (query = {}) => {
    let results = [...mockDB.users];
    if (query.is_premium !== undefined) {
      results = results.filter(user => user.is_premium === query.is_premium);
    }
    return results;
  },
  countDocuments: async (query = {}) => {
    let count = mockDB.users.length;
    if (query.is_premium !== undefined) {
      count = mockDB.users.filter(user => user.is_premium === query.is_premium).length;
    }
    return count;
  },
  findOneAndUpdate: async (query, update, options) => {
    let user = mockDB.users.find(u => u.telegram_id === query.telegram_id);
    if (!user) {
      user = {
        _id: Date.now().toString(),
        telegram_id: query.telegram_id,
        name: update.$set?.name || 'Demo User',
        username: update.$set?.username || null,
        language: update.$set?.language || 'hi',
        is_premium: update.$set?.is_premium || false,
        created_at: new Date(),
        last_active: new Date(),
        settings: update.$set?.settings || {
          voice_enabled: true,
          notifications: true,
          theme: 'auto'
        }
      };
      mockDB.users.push(user);
    } else {
      Object.assign(user, update.$set || {});
      user.last_active = new Date();
    }
    return user;
  },
  create: async (data) => {
    const user = {
      _id: Date.now().toString(),
      ...data,
      created_at: new Date(),
      last_active: new Date()
    };
    mockDB.users.push(user);
    return user;
  }
};

// Chat History Schema (Mock)
const MockChat = {
  find: async (query = {}) => {
    let results = [...mockDB.chats];
    if (query.telegram_id) {
      results = results.filter(chat => chat.telegram_id === query.telegram_id);
    }
    if (query.timestamp && query.timestamp.$gte) {
      results = results.filter(chat => new Date(chat.timestamp) >= query.timestamp.$gte);
    }
    return results.slice(-50); // Limit to last 50
  },
  countDocuments: async (query = {}) => {
    let count = mockDB.chats.length;
    if (query.timestamp && query.timestamp.$gte) {
      count = mockDB.chats.filter(chat => new Date(chat.timestamp) >= query.timestamp.$gte).length;
    }
    return count;
  },
  create: async (data) => {
    const chat = {
      _id: Date.now().toString(),
      ...data,
      timestamp: new Date()
    };
    mockDB.chats.push(chat);
    return chat;
  },
  aggregate: async (pipeline) => {
    // Simple mock aggregation for date grouping
    const results = [];
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      results.push({
        _id: dateStr,
        count: Math.floor(Math.random() * 20) + 5
      });
    }
    return results;
  }
};

// Payment Schema (Mock)
const MockPayment = {
  find: async (query = {}) => {
    let results = [...mockDB.payments];
    if (query.status) {
      results = results.filter(payment => payment.status === query.status);
    }
    return results;
  },
  create: async (data) => {
    const payment = {
      _id: Date.now().toString(),
      ...data,
      created_at: new Date()
    };
    mockDB.payments.push(payment);
    return payment;
  },
  aggregate: async (pipeline) => {
    // Mock revenue aggregation
    const results = [];
    const now = new Date();
    for (let i = 6; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      results.push({
        _id: dateStr,
        total: Math.floor(Math.random() * 5000) + 1000
      });
    }
    return results;
  }
};

// Session Schema (Mock)
const MockSession = {
  findOne: async (query) => {
    return mockDB.sessions.find(session =>
      session.telegram_id === query.telegram_id
    ) || null;
  },
  findOneAndUpdate: async (query, update, options) => {
    let session = mockDB.sessions.find(s => s.telegram_id === query.telegram_id);
    if (!session) {
      session = {
        _id: Date.now().toString(),
        telegram_id: query.telegram_id,
        ...update.$set,
        created_at: new Date()
      };
      mockDB.sessions.push(session);
    } else {
      Object.assign(session, update.$set || {});
    }
    return session;
  }
};

// Connect to database (Mock)
async function connectDB() {
  try {
    console.log('🔄 Using mock database for demo purposes...');
    console.log('✅ Mock database connected successfully');

    // Add some demo data
    if (mockDB.users.length === 0) {
      mockDB.users.push({
        _id: '1',
        telegram_id: 123456789,
        name: 'Demo Admin',
        username: 'demo_admin',
        language: 'hi',
        is_premium: true,
        isAdmin: true,
        created_at: new Date(),
        last_active: new Date(),
        settings: {
          voice_enabled: true,
          notifications: true,
          theme: 'auto'
        }
      });

      mockDB.users.push({
        _id: '2',
        telegram_id: 987654321,
        name: 'Demo User',
        username: 'demo_user',
        language: 'en',
        is_premium: false,
        created_at: new Date(Date.now() - 86400000), // 1 day ago
        last_active: new Date(),
        settings: {
          voice_enabled: true,
          notifications: true,
          theme: 'light'
        }
      });
    }

    return true;
  } catch (error) {
    console.error('Mock database connection error:', error);
    throw error;
  }
}

// Export mock models
const User = MockUser;
const Chat = MockChat;
const Payment = MockPayment;
const Session = MockSession;

module.exports = {
  connectDB,
  User,
  Chat,
  Payment,
  Session
};