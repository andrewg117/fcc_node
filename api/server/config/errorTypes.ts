export default class HttpTypeError extends TypeError {
  public statusCode: number;

  constructor(message: string, statusCode = 400) {
    super(message);
    this.statusCode = statusCode;
    
    // Restores proper prototype chain in older TS targets
    Object.setPrototypeOf(this, new.target.prototype);
  }
}