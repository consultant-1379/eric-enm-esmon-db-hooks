//This code will create the new postgres Database
import pg from 'pg';
import log4js from 'log4js';

const logger = log4js.getLogger('init');

(async () => {
  let client;

  try {
  const host = 'postgres'
  const port = 5432
  const adminUser = 'postgres'
  const password = process.env.ESM_PGADMIN_PASSWORD
  const newUser = process.env.ESM_PGUSER_USERNAME
  const newPassword = process.env.ESM_PGUSER_PASSWORD
  const newDatabase = 'eric-esm-server'

  const clientConfig = {
    host,
    port,
    password,
    user: adminUser
  };

  client = new pg.Client(clientConfig);
  await client.connect();

  try {
    await client.query(
          `CREATE USER "${newUser}" WITH ENCRYPTED PASSWORD '${newPassword}';`
        );
        logger.info(`User created: ${newUser}`);
  } catch (error) {
    // 42710 means the user already exists, which is fine
    if (!(error instanceof pg.DatabaseError) || error.code !== '42710')
          throw error;
  }

  try {
    await client.query(`CREATE DATABASE "${newDatabase}" OWNER "${newUser}"`);
        logger.info(`Database created: ${newDatabase}`);
  } catch (error) {
    // 42P04 means the database already exists, which is fine
    if (!(error instanceof pg.DatabaseError) || error.code !== '42P04')
          throw error;
  }
   try {
    await client.query(
          `GRANT ALL PRIVILEGES ON DATABASE "${newDatabase}" to "${newUser}";`
        );
        logger.info(`Granted Priviledges to : ${newUser}`);
  } catch (error) {
          logger.error(error);
  }
 } catch (error) {
   logger.error(error);
   process.exit(1);
 } finally {
   logger.info('Closing the client');
   client?.end();
 }
})();
