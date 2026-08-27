import express, { Request, Response, NextFunction } from 'express';
import HttpTypeError from '../config/errorTypes';

const routes = express.Router();

routes.get("/", (req: Request, res: Response) => {
    res.status(200).send("Server home\n");
});

routes.get("/user/:id", (req: Request, res: Response, next: NextFunction) => {
    console.log(`Searching for User: ${req.params.id}`)
    const userID = Number(req.params.id);
    

    if (isNaN(userID)) {
        let numError = new HttpTypeError("Id given is not a number", 404);
        return next(numError);
    }

    res.status(200).send(`User ID: ${userID}`);
});


export default routes;