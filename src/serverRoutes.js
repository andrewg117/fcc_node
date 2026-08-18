import express from 'express';

const routes = express.Router();

routes.get("/", (req, res) => {
    res.status(200).send("Server home\n");
});

routes.get("/user/:id", (req, res, next) => {
    console.log(`Searching for User: ${req.params.id}`)
    const userID = Number(req.params.id);
    

    if (isNaN(userID)) {
        let numError = new TypeError("Id given is not a number");
        numError.statusCode = 404;
        return next(numError);
    }

    res.status(200).send(`User ID: ${userID}`);
});


export default routes;