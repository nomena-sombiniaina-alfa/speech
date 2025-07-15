const express = require('express');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const path = require('path');
const { Sequelize, DataTypes } = require('sequelize');

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

// Middleware pour exposer le statut de connexion à toutes les vues
app.use((req, res, next) => {
    res.locals.isLoggedIn = !!req.cookies.sessionId;
    next();
});

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middleware d'authentification
const isAuthenticated = (req, res, next) => {
    if (req.cookies.sessionId) return next();
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
    const user = await User.findOne({ where: { username, password } });
    if (user) {
        res.cookie('sessionId', `${user.id}-${Date.now()}`, { httpOnly: false }); // Cookie non sécurisé pour la démo
        res.redirect('/products');
    } else {
        res.status(401).send('Identifiants incorrects');
    }
});

app.post('/logout', (req, res) => {
    res.clearCookie('sessionId');
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
    const sessionId = req.cookies.sessionId;
    const userId = sessionId.split('-')[0];

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
    await Product.create({ name: 'Article de luxe', description: 'Un produit très cher.' });
    await Product.create({ name: 'Super Widget', description: 'Un autre article incroyable.' });
    
    console.log('Données initiales insérées.');

    app.listen(port, () => {
        console.log(`Serveur vulnérable en écoute sur http://localhost:${port}`);
        console.log(`Accédez à http://localhost:${port} pour commencer.`);
    });
});
