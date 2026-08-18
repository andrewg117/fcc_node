import express from 'express';
import serverRoutes from './src/serverRoutes.js'

const app = express();
const PORT = 3000


app.use("/server", (req, res, next) => {
    console.log(`Server request called ${req.method} to ${req.originalUrl}`)
    next();
});

app.use("/server", serverRoutes);

app.use((req, res, next) => {
  // Create a 404 Error object
  const error = new Error(`Cannot ${req.method} ${req.originalUrl}`);
  error.statusCode = 404;
  error.name = "NotFoundError";

  // Pass it to the global error handler
  next(error); 
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

app.listen(PORT, () => {
    console.log(`Server running on port: ${PORT}`)
});