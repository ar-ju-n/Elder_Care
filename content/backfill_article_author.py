from accounts.models import User
from content.models import Article

def run():
    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        print('No superuser found!')
        return
    updated = Article.objects.filter(author__isnull=True).update(author=admin)
    print(f"Updated {updated} articles with missing author.")

if __name__ == "__main__":
    run()
