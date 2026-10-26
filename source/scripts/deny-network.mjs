// Verification preload: fail if any Node network API is used. This changes only this child process.
import http from 'node:http';
import https from 'node:https';
import net from 'node:net';
import tls from 'node:tls';
import dns from 'node:dns';
import { syncBuiltinESMExports } from 'node:module';
const denied = () => { throw new Error('NETWORK_DISABLED_FOR_PORTABLE_VERIFICATION'); };
globalThis.fetch = denied;
http.request = denied; http.get = denied; https.request = denied; https.get = denied;
net.connect = denied; net.createConnection = denied; net.Socket.prototype.connect = denied;
tls.connect = denied; dns.lookup = denied; dns.resolve = denied;
syncBuiltinESMExports();
