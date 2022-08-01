from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Follow, Post, Group, User
from django.core.paginator import Paginator
from posts.forms import PostForm, CommentForm
from django.views.decorators.cache import cache_page
from django.urls import reverse


def to_paginate(p_iterable, page_number, posts_a_page=10):
    paginator = Paginator(p_iterable, posts_a_page)
    return paginator.get_page(page_number)


@cache_page(20, key_prefix='index_page')
def index(request):
    posts_list = Post.objects.all()
    page_num_from_url = request.GET.get('page')

    page_obj = to_paginate(posts_list, page_num_from_url)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_lists = group.posts.all()
    page_num_from_url = request.GET.get('page')

    page_obj = to_paginate(post_lists, page_num_from_url)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.select_related('group').all()
    page_num_from_url = request.GET.get('page')

    page_obj = to_paginate(post_list, page_num_from_url)

    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=user,
        ).exists()

    context = {
        'author': user,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': CommentForm,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', username=request.user.username)

    form = PostForm()
    return render(request, 'posts/create_post.html', {
        'form': form,
        'is_edit': False
    })


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=post)
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    return render(request, 'posts/create_post.html',
                  {'form': form,
                   'is_edit': True,
                   'post_id': post_id,
                   })


@login_required
def add_comment(request, post_id):
    # Получите пост
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    favs = Follow.objects.filter(user=request.user).select_related('author')
    favs = [entry.author for entry in favs]
    posts_list = Post.objects.filter(author__in=favs)
    page_num_from_url = request.GET.get('page')

    page_obj = to_paginate(posts_list, page_num_from_url)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    sub = Follow.objects.filter(user=request.user, author=author).count()
    if author != request.user and sub == 0:
        Follow.objects.create(
            user=request.user,
            author=author,
        )
    return redirect(reverse('posts:profile', args=(username,)))


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=request.user, author=author)
    follow.delete()
    return redirect(reverse('posts:profile', args=(username,)))
