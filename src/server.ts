import app from "./server/app.js";

const PORT = 3000

app.listen(PORT, () => {
    console.log(`\n Server running on http://localhost:3000`)
});