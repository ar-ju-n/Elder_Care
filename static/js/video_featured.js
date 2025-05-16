document.querySelectorAll('.video-card-js').forEach(function(card) {
  card.addEventListener('click', function() {
    var featuredTitle = document.getElementById('featured-title');
    var featuredVideo = document.getElementById('featured-video');
    var featuredSource = document.getElementById('featured-source');
    var featuredDescription = document.getElementById('featured-description');
    var featuredDate = document.getElementById('featured-date');
    var featuredAuthor = document.getElementById('featured-author');

    featuredTitle.textContent = 'Featured: ' + this.getAttribute('data-title');
    featuredSource.setAttribute('src', this.getAttribute('data-url'));
    featuredVideo.load();
    featuredDescription.textContent = this.getAttribute('data-description');
    featuredDate.textContent = this.getAttribute('data-date');
    featuredAuthor.textContent = this.getAttribute('data-author');

    window.scrollTo({ top: document.getElementById('featured-video-container').offsetTop - 60, behavior: 'smooth' });
  });
});
