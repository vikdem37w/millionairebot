const { Client } = require("pg");

const client = new Client({
  host: "localhost",
  user: process.env.DB_USER,
  port: 5432,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
});

client.connect();

client.query(`SELECT * FROM users`, (error, result) => {
  if(!error) {
    console.log(result.rows);
  } else {
    console.log(error.message);
  }
  client.end();
});