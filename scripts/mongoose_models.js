/**
 * QueryMind AI — Mongoose Schemas & Models
 *
 * This file defines the complete Mongoose models matching the QueryMind AI backend.
 * You can require/import this file in any Node.js/Express service, or execute it directly
 * with Node.js to create the schemas and test your MongoDB Atlas connection.
 *
 * Usage:
 *   node scripts/mongoose_models.js "mongodb+srv://<user>:<password>@cluster.mongodb.net/querymind"
 */

const mongoose = require('mongoose');
const { Schema } = mongoose;

// ============================================================================
// 1. User Model
// ============================================================================
const UserSchema = new Schema(
  {
    name: {
      type: String,
      required: [true, 'Full name is required'],
      trim: true,
      maxlength: 200,
    },
    email: {
      type: String,
      required: [true, 'Email address is required'],
      unique: true,
      lowercase: true,
      trim: true,
      index: true,
    },
    password_hash: {
      type: String,
      required: [true, 'Password hash is required'],
    },
    role: {
      type: String,
      enum: ['admin', 'analyst', 'viewer'],
      default: 'viewer',
      index: true,
    },
    status: {
      type: String,
      enum: ['active', 'suspended', 'deactivated'],
      default: 'active',
    },
    title: {
      type: String,
      default: 'Database Analyst',
      trim: true,
    },
    department: {
      type: String,
      default: 'Analytics & Data Platform',
      trim: true,
    },
    avatar: {
      type: String,
      default: 'QM',
      trim: true,
    },
    bio: {
      type: String,
      default: '',
      maxlength: 250,
    },
    phone: {
      type: String,
      default: '',
    },
    location: {
      type: String,
      default: 'Ahmedabad, India',
    },
  },
  {
    collection: 'users',
    timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' },
  }
);

// ============================================================================
// 2. Database Connection Model
// ============================================================================
const DatabaseConnectionSchema = new Schema(
  {
    name: {
      type: String,
      required: [true, 'Connection name is required'],
      trim: true,
      maxlength: 200,
    },
    db_type: {
      type: String,
      required: true,
      enum: ['mongodb', 'mysql', 'postgresql'],
      default: 'mysql',
      lowercase: true,
      index: true,
    },
    // SQL host and port
    host: { type: String, default: null },
    port: { type: Number, default: null },
    database_name: { type: String, default: null },
    username: { type: String, default: null },
    password_encrypted: { type: String, default: null }, // Fernet encrypted string
    // MongoDB connection URI
    connection_string_encrypted: { type: String, default: null }, // Fernet encrypted URI
    created_by: {
      type: String,
      required: true,
      index: true,
    },
    status: {
      type: String,
      enum: ['connected', 'disconnected', 'error'],
      default: 'disconnected',
    },
    last_connected_at: { type: Date, default: null },
    schemas: [
      {
        table_name: String,
        columns: [
          {
            name: String,
            data_type: String,
            is_nullable: Boolean,
            is_primary_key: Boolean,
          },
        ],
      },
    ],
  },
  {
    collection: 'database_connections',
    timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' },
  }
);

// ============================================================================
// 3. Schema Access / Table-Level Permissions Model
// ============================================================================
const SchemaAccessSchema = new Schema(
  {
    database_id: {
      type: String,
      required: true,
      index: true,
    },
    table_name: {
      type: String,
      required: true,
    },
    allowed_roles: {
      type: [String],
      default: ['admin', 'analyst', 'viewer'],
    },
    is_sensitive: {
      type: Boolean,
      default: false,
    },
    columns: [
      {
        name: String,
        data_type: String,
        is_nullable: Boolean,
        is_primary_key: Boolean,
      },
    ],
  },
  {
    collection: 'schema_access',
    timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' },
  }
);
SchemaAccessSchema.index({ database_id: 1, table_name: 1 }, { unique: true });

// ============================================================================
// 4. Query Session Model
// ============================================================================
const QuerySessionSchema = new Schema(
  {
    user_id: {
      type: String,
      required: true,
      index: true,
    },
    database_id: {
      type: String,
      default: null,
      index: true,
    },
    title: {
      type: String,
      default: 'New Query Session',
      trim: true,
      maxlength: 250,
    },
  },
  {
    collection: 'query_sessions',
    timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' },
  }
);

// ============================================================================
// 5. Query Model (Executed & Generated Queries)
// ============================================================================
const StatementInfoSchema = new Schema(
  {
    statement_index: { type: Number, default: 0 },
    sql: { type: String, required: true },
    operation: {
      type: String,
      enum: ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'UNKNOWN'],
      default: 'SELECT',
    },
    validation_status: {
      type: String,
      enum: ['valid', 'invalid', 'warning', 'blocked'],
      default: 'valid',
    },
    validation_message: { type: String, default: null },
    approval_status: {
      type: String,
      enum: ['pending', 'approved', 'rejected'],
      default: 'pending',
    },
    warning_broad_impact: { type: Boolean, default: false },
    affected_table: { type: String, default: null },
    tables: { type: [String], default: [] },
    mql: { type: Schema.Types.Mixed, default: null }, // MongoDB MQL pipeline or filter
    estimated_rows_affected: { type: Number, default: null },
  },
  { _id: false }
);

const QuerySchema = new Schema(
  {
    user_id: {
      type: String,
      required: true,
      index: true,
    },
    database_id: {
      type: String,
      default: null,
      index: true,
    },
    session_id: {
      type: String,
      default: null,
      index: true,
    },
    nl_query: {
      type: String,
      required: [true, 'Natural language prompt is required'],
    },
    input_type: {
      type: String,
      enum: ['text', 'voice'],
      default: 'text',
    },
    language: {
      type: String,
      enum: ['English', 'Hinglish'],
      default: 'English',
    },
    status: {
      type: String,
      enum: ['generated', 'executed', 'failed', 'pending_confirmation', 'cancelled'],
      default: 'generated',
    },
    statements: [StatementInfoSchema],
    columns: { type: [String], default: [] },
    rows: { type: [[Schema.Types.Mixed]], default: [] },
    row_count: { type: Number, default: 0 },
    execution_time_ms: { type: Number, default: 0 },
    summary: { type: String, default: null },
    error_message: { type: String, default: null },
    truncated: { type: Boolean, default: false },
    max_allowed_rows: { type: Number, default: 1000 },
    clarification_needed: { type: Boolean, default: false },
    clarification_question: { type: String, default: null },
    clarification_choices: { type: [String], default: [] },
  },
  {
    collection: 'queries',
    timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' },
  }
);
QuerySchema.index({ created_at: -1 });

// ============================================================================
// 6. Query Log / Audit Security Log Model
// ============================================================================
const QueryLogSchema = new Schema(
  {
    query_id: {
      type: String,
      default: null,
      index: true,
    },
    user_id: {
      type: String,
      required: true,
      index: true,
    },
    database_id: {
      type: String,
      default: null,
    },
    event: {
      type: String,
      required: true,
    },
    severity: {
      type: String,
      enum: ['low', 'medium', 'high', 'critical'],
      default: 'low',
      index: true,
    },
    status: {
      type: String,
      default: 'logged',
    },
    details: {
      type: Schema.Types.Mixed,
      default: {},
    },
  },
  {
    collection: 'query_logs',
    timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' },
  }
);
QueryLogSchema.index({ created_at: -1 });

// ============================================================================
// 7. User Settings Model
// ============================================================================
const UserSettingsSchema = new Schema(
  {
    user_id: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    confirm_updates: {
      type: Boolean,
      default: true,
    },
    confirm_deletes: {
      type: Boolean,
      default: true,
    },
    row_limit: {
      type: Number,
      default: 100,
    },
    query_timeout: {
      type: Number,
      default: 30, // seconds
    },
  },
  {
    collection: 'user_settings',
    timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' },
  }
);

// ============================================================================
// 8. Role Request Model
// ============================================================================
const RoleRequestSchema = new Schema(
  {
    user_id: {
      type: String,
      required: true,
      index: true,
    },
    user_name: {
      type: String,
      required: true,
    },
    user_email: {
      type: String,
      required: true,
    },
    current_role: {
      type: String,
      enum: ['viewer', 'analyst', 'admin'],
      required: true,
    },
    requested_role: {
      type: String,
      enum: ['analyst', 'admin'],
      required: true,
    },
    reason: {
      type: String,
      required: true,
    },
    status: {
      type: String,
      enum: ['pending', 'approved', 'rejected'],
      default: 'pending',
      index: true,
    },
    reviewed_by: {
      type: String,
      default: null,
    },
    reviewed_at: {
      type: Date,
      default: null,
    },
  },
  {
    collection: 'role_requests',
    timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' },
  }
);
RoleRequestSchema.index({ created_at: -1 });

// ============================================================================
// Export Models
// ============================================================================
const User = mongoose.model('User', UserSchema);
const DatabaseConnection = mongoose.model('DatabaseConnection', DatabaseConnectionSchema);
const SchemaAccess = mongoose.model('SchemaAccess', SchemaAccessSchema);
const QuerySession = mongoose.model('QuerySession', QuerySessionSchema);
const Query = mongoose.model('Query', QuerySchema);
const QueryLog = mongoose.model('QueryLog', QueryLogSchema);
const UserSettings = mongoose.model('UserSettings', UserSettingsSchema);
const RoleRequest = mongoose.model('RoleRequest', RoleRequestSchema);

module.exports = {
  User,
  DatabaseConnection,
  SchemaAccess,
  QuerySession,
  Query,
  QueryLog,
  UserSettings,
  RoleRequest,
};

// ============================================================================
// Self-Executing CLI Runner
// ============================================================================
if (require.main === module) {
  const targetUri =
    process.argv[2] ||
    process.env.MONGODB_URI ||
    'mongodb://localhost:27017/querymind';

  console.log('\n======================================================');
  console.log('   QueryMind AI — Mongoose Schema Initializer');
  console.log('======================================================');
  console.log(`Connecting to: ${targetUri.replace(/:\/\/[^@]+@/, '://***:***@')}`);

  mongoose
    .connect(targetUri, { serverSelectionTimeoutMS: 8000 })
    .then(async () => {
      console.log('[✓] Connected to MongoDB via Mongoose!');
      console.log('\nRegistering and syncing indexes for 8 models:');

      const models = [
        { name: 'User', model: User },
        { name: 'DatabaseConnection', model: DatabaseConnection },
        { name: 'SchemaAccess', model: SchemaAccess },
        { name: 'QuerySession', model: QuerySession },
        { name: 'Query', model: Query },
        { name: 'QueryLog', model: QueryLog },
        { name: 'UserSettings', model: UserSettings },
        { name: 'RoleRequest', model: RoleRequest },
      ];

      for (const m of models) {
        await m.model.init();
        console.log(`  [✓] Model compiled & indexes synced: ${m.name}`);
      }

      console.log('\nAll 8 Mongoose models ready on MongoDB Atlas!');
      await mongoose.disconnect();
      console.log('Connection closed cleanly.\n');
      process.exit(0);
    })
    .catch((err) => {
      console.error('[!] Mongoose connection error:', err.message);
      process.exit(1);
    });
}
