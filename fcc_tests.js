import path from "path";

//#region  Testing path
console.log("Testing path..");
const filename = import.meta.filename;
const dirname = import.meta.dirname;

console.log(filename);
console.log(path.basename(filename));

console.log(path.basename(dirname));

let fileParse = path.parse(filename);

console.log(fileParse.base);
//#endregion

//#region Testing process
console.log("\nTesting process..");

console.log(process.env.SHELL);

//#endregion