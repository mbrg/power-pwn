function getArguments() {
    const args = process.argv.slice(2);

    if (args.length < 2) {
        console.error("Too few arguments. Please provide the username and password as arguments in the following format: 'user=<your_user> password=<your_password>'.");
        process.exit(1);
    }
    user = getSingleArgument(args, "user")
    password = getSingleArgument(args, "password")

    return {
        "user": user,
        "password": password
    }
}

function getSingleArgument(args, argumentName) {
    argNameToSearch = `${argumentName}=`

    arg = args.filter(arg => arg.includes(argNameToSearch))
    if (arg.length === 0) {
        console.error(`Argument ${argumentName} not found`);
        process.exit(1);
    }
    return arg[0].split("=")[1]
}



module.exports = {
    getArguments
};
