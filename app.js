import express from 'express';
import path from 'path';
import serverRoutes from './routes/serverRoutes.js';

const app = express();


app.use((req, res, next) => {
    console.log(`Server request called ${req.method} to ${req.originalUrl}`)
    next();
});

app.use("/server", serverRoutes);

app.use((req, res, next) => {
  res.status(404).sendFile(path.join(import.meta.dirname, "views", "RouteNotFound.html"));
});

app.use((err, req, res, next) => {

    // Determine the HTTP status code (default to 500 Server Error)
    const statusCode = err.statusCode || 500;

    // Send a standardized JSON response to the client
    res.status(statusCode).json({
        code: statusCode,
        "type": err.name,
        message: err.message || "Internal Server Error",
    });
});

export default app;