var gulp = require('gulp');
var flatten = require('gulp-flatten');
var less = require('gulp-sources-less');
var sourcemaps = require('gulp-sourcemaps');
var path = require('path');
var argv = require('yargs').argv;
var minifyCSS = require('gulp-minify-css');
var requirejsOptimize = require('gulp-requirejs-optimize');
var concat = require('gulp-concat');
var svg = require('gulp-svg-inline-css');
var clean = require('gulp-clean');
var execSync = require('child_process').execSync;

var staticDir = '../static',
  jsDir = path.join(staticDir, '/js'),
  cssDir = path.join(staticDir, '/css'),
  gifDir = path.join(staticDir, '/img/gif'),
  optimizeModules = [
    'thread.js',
    'editor-bootstrap.js',
    'base.js'
  ];

var ISSConfig = JSON.parse(
    execSync('python manage.py dump_iss_config',
             {
               cwd: '../..',
               encoding: 'UTF-8'
             }));

gulp.task('clean', function() {
  return gulp.src([ gifDir, cssDir, jsDir ])
    .pipe(clean({read: false, force: true}));
});
 
gulp.task('icons', function() {
  return gulp.src('src/assets/svg/*.svg')
    .pipe(svg({
      className: '.icn-%s()'
    }))
    .pipe(concat('icons.less'))
    .pipe(gulp.dest('src/base'));
});

gulp.task('smilies', function() {
  return gulp.src('src/assets/gif/*')
    .pipe(gulp.dest(gifDir));
});

gulp.task('less', ['icons'], function() {

  var lessStream = less({
      paths: [ path.join(__dirname, 'less') ]
    }).on('error', function(err) {
      console.error(err);
      this.emit('end');
    });

  var stream = gulp.src('./src/combined/combined.less');

  stream = argv.optimize ? stream : stream.pipe(sourcemaps.init());
  stream = stream.pipe(lessStream);
  stream = argv.optimize ? stream : stream.pipe(sourcemaps.write());
  stream = stream.pipe(flatten());
  stream = argv.optimize ? stream.pipe(minifyCSS()) : stream;
  stream = stream.pipe(gulp.dest(cssDir));

  return stream;
});

gulp.task('javascript', function() {
  return gulp.src('./src/**/*.js')
    .pipe(flatten())
    .pipe(gulp.dest(jsDir));
});

gulp.task('optimize-js', ['javascript'], function() {
  var optPaths = optimizeModules.map(function(moduleName) {
    return path.join(jsDir, moduleName);
  });

  return gulp.src(optPaths)
    .pipe(requirejsOptimize({ paths: { 'jquery': 'empty:' } }))
    .pipe(gulp.dest('../static/js'))
    .pipe(requirejsOptimize({ optimize: 'none' }))
    .pipe(flatten())
    .pipe(gulp.dest('../static/js'));
});

gulp.task('generate-extensions', [], function() {
  for (var i=0; i<ISSConfig.extensions.length; i++) {
    var ext = ISSConfig.extensions[i],
      extConfig = ISSConfig.extension_config[ext];

    if ('gulp_dir' in extConfig) {
      console.log(extConfig.gulp_dir);
      execSync('npm run-script build', {cwd: extConfig.gulp_dir});
    }
  }
});

var generateTasks = ['less', 'smilies', 'generate-extensions'];
generateTasks.push(argv.optimize ? 'optimize-js' : 'javascript');
gulp.task('generate', generateTasks);

gulp.task('watch', ['generate'], function() {
  gulp.watch([ './src/assets/svg/*.svg' ], ['icons']);
  gulp.watch([ './src/assets/gif/*' ], ['smilies']);
  gulp.watch([ './src/**/*.less' ], ['less']);
  gulp.watch([ './src/**/*.js' ], ['javascript']);
});
