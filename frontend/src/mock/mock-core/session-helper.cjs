const path = require("path");
const Mock = require("mockjs");
const session = require("express-session");
const FileStore = require("session-file-store")(session);

const { isFunction } = require("lodash");

const argv = require("minimist")(process.argv.slice(2));
const isDev = (argv.env || "development") === "development";
const TOKEN_KEY = isDev ? "X-Auth-Token" : "X-Csrf-Token";

const setSessionUser = (req, getLoginInfo) => {
  if (!isFunction(getLoginInfo)) {
    throw new Error("getLoginInfo must be a function");
  }

  if (!req.session?.users) {
    req.session.users = {};
  }

  let token = req.get(TOKEN_KEY);
  const { users } = req.session;
  if (!token || !users[token]) {
    token = Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, "");
    const userInfo = getLoginInfo(req) || {};
    users[token] = user;
  }
  return token;
};

const getSessionUser = (req) => {
  const token = req.get(TOKEN_KEY);
  if (token && req.session?.users) {
    return req.session.users[token];
  }
  return null;
};

const genExpressSession = () => {
  return session({
    name: "demo.name",
    secret: "demo.secret",
    resave: true,
    saveUninitialized: true,
    cookie: {
      maxAge: 60 * 60 * 1e3,
      expires: new Date(Date.now() + 60 * 60 * 1e3),
    }, // 1 hour
    store: new FileStore({
      path: path.join(__dirname, "../sessions"),
      retries: 0,
      keyFunction: (secret, sessionId) => {
        return secret + sessionId;
      },
    }),
  });
};

module.exports = {
  setSessionUser,
  getSessionUser,
  genExpressSession,
};
