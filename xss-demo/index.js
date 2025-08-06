const express = require('express');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const path = require('path');
const { Sequelize, DataTypes } = require('sequelize');
const helmet = require('helmet');

const app = express();
const port = 3000;

// Configuration de la base de données
const sequelize = new Sequelize({
    dialect: 'sqlite',
    storage: './database.sqlite',
    logging: false // Masquer les logs SQL pour plus de clarté
});

// Modèles
const User = sequelize.define('User', {
    username: { type: DataTypes.STRING, allowNull: false, unique: true },
    password: { type: DataTypes.STRING, allowNull: false }
});

const Product = sequelize.define('Product', {
    name: { type: DataTypes.STRING, allowNull: false },
    description: { type: DataTypes.TEXT, allowNull: false },
    image: { type: DataTypes.STRING }
});

const Comment = sequelize.define('Comment', {
    text: { type: DataTypes.TEXT, allowNull: false }
});

// Associations
User.hasMany(Comment);
Comment.belongsTo(User);
Product.hasMany(Comment);
Comment.belongsTo(Product);

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

// Configuration de la Content Security Policy (CSP)
app.use(helmet.contentSecurityPolicy({
    directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'", "https://cdn.jsdelivr.net"], // Autoriser les scripts de Bootstrap
        styleSrc: ["'self'", "https://cdn.jsdelivr.net"],
        fontSrc: ["'self'", "https://cdn.jsdelivr.net"],
        imgSrc: ["'self'", "data:"]
    }
}));

// Middleware pour exposer le statut de connexion et l'utilisateur à toutes les vues
app.use(async (req, res, next) => {
    res.locals.isLoggedIn = !!req.cookies.userData;
    res.locals.user = null;
    if (res.locals.isLoggedIn) {
        try {
            const userData = Buffer.from(req.cookies.userData, 'base64').toString('utf8');
            res.locals.user = JSON.parse(userData);
        } catch (error) {
            console.error("Erreur lors du décodage des données utilisateur:", error);
            res.clearCookie('userData'); // Efface le cookie corrompu
            res.locals.isLoggedIn = false;
        }
    }
    next();
});

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middleware d'authentification
const isAuthenticated = (req, res, next) => {
    if (req.cookies.userData) return next();
    res.redirect('/login');
};

// Routes
app.get('/', (req, res) => res.redirect('/products'));

app.get('/login', (req, res) => {
    if (res.locals.isLoggedIn) {
        return res.redirect('/products');
    }
    res.render('login');
});

app.post('/login', async (req, res) => {
    const { username, password } = req.body;

    try {
        // CORRECTION: Utilisation de requêtes paramétrées pour prévenir les injections SQL.
        // Sequelize assainit les entrées, ce qui empêche les attaquants de manipuler la requête.
        const user = await User.findOne({ where: { username, password } });
        
        console.log('user:', user);

        if (user) {
            // VULNÉRABILITÉ: Stockage des données utilisateur sensibles dans un cookie
            // Toutes les données de l'utilisateur, y compris le mot de passe, sont encodées en Base64 et stockées.
            // Cela expose des informations sensibles qui peuvent être facilement décodées.
            const userData = Buffer.from(JSON.stringify(user.get({ plain: true }))).toString('base64');
            res.cookie('userData', userData, { 
                httpOnly: true, // Empêche l'accès au cookie via JavaScript
                sameSite: 'strict' // Prévient les attaques CSRF
            });
            res.redirect('/products');
        } else {
            res.status(401).send('Identifiants incorrects');
        }
    } catch (error) {
        console.error("Erreur de connexion:", error);
        res.status(500).send("Une erreur est survenue lors de la tentative de connexion.");
    }
});

app.post('/logout', (req, res) => {
    res.clearCookie('userData');
    res.redirect('/login');
});

app.get('/products', isAuthenticated, async (req, res) => {
    const products = await Product.findAll();
    res.render('product_list', { products });
});

app.get('/products/:id', isAuthenticated, async (req, res) => {
    const product = await Product.findByPk(req.params.id, {
        include: [{
            model: Comment,
            include: User
        }],
        order: [[Comment, 'createdAt', 'ASC']]
    });
    if (product) {
        res.render('product', { product, comments: product.Comments });
    } else {
        res.status(404).send('Produit non trouvé');
    }
});

app.post('/products/:id/comments', isAuthenticated, async (req, res) => {
    const { text } = req.body;
    
    // Assure que les informations de l'utilisateur sont disponibles
    if (!res.locals.user) {
        return res.status(401).send("Session invalide, veuillez vous reconnecter.");
    }
    const userId = res.locals.user.id;

    try {
        await Comment.create({
            text,
            ProductId: req.params.id,
            UserId: userId
        });
        res.redirect(`/products/${req.params.id}`);
    } catch (error) {
        console.error("Erreur lors de la création du commentaire:", error);
        res.status(500).send("Impossible de poster le commentaire.");
    }
});

// Initialisation de la DB et démarrage du serveur
sequelize.sync({ force: true }).then(async () => {
    console.log('Base de données synchronisée.');
    
    await User.create({ username: 'admin', password: 'password' });
    await User.create({ username: 'user', password: 'password' });
    await User.create({ username: 'user2', password: 'password' });
    await Product.create({ name: 'Article de luxe', description: 'Un produit très cher.' });
    await Product.create({ name: 'Super Widget', description: 'Un autre article incroyable.' });
    
    console.log('Données initiales insérées.');

    app.listen(port, () => {
        console.log(`Serveur vulnérable en écoute sur http://localhost:${port}`);
        console.log(`Accédez à http://localhost:${port} pour commencer.`);
    });
});
