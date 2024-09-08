import uvicorn

from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi_pagination import add_pagination, paginate, Params

from app.database import *
from sqlalchemy import select, insert, update
from sqlalchemy.orm import Session

from typing import Annotated
from fastapi.templating import Jinja2Templates

app = FastAPI()
add_pagination(app)
templates = Jinja2Templates(directory='app/templates')
curr_user = None


@app.get('/')
async def main_page(request: Request) -> HTMLResponse:
    global curr_user
    info = {}
    context = {
        'request': request,
        'info': info,
        'user': curr_user,
    }
    return templates.TemplateResponse('main_page.html', context=context)


@app.get('/registration')
async def get_signup_page(request: Request) -> HTMLResponse:
    context = {
        'request': request,
        'user': curr_user,
        'info': {},
    }
    return templates.TemplateResponse('registration_page.html', context=context)


@app.post('/registration')
async def post_signup_page(request: Request,
                           username: Annotated[str, Form()],
                           password: Annotated[str, Form()],
                           repeat_password: Annotated[str, Form()],
                           age: Annotated[int, Form()],
                           db: Annotated[Session, Depends(get_db)]):
    global curr_user
    check_user = db.scalars(select(Buyer).where(Buyer.name == username)).first()
    error = {}
    if curr_user is None:
        if check_user is not None:
            error.update({'error': 'Пользователь с таким именем существует'})
        elif password != repeat_password:
            error.update({'error': 'Пароли не совпадают'})
        else:
            db.execute(insert(Buyer).values(name=username,
                                            password=password,
                                            age=age))
            db.commit()
            curr_user = check_user
            return RedirectResponse('/', status_code=302)

    context = {
        'request': request,
        'error': error,
        'user': curr_user,
    }
    return templates.TemplateResponse('registration_page.html', context=context)


@app.get('/login')
async def get_login_page(request: Request) -> HTMLResponse:
    context = {
        'request': request,
        'user': curr_user,
        'info': {},
    }
    return templates.TemplateResponse('login_page.html', context=context)


@app.post('/login')
async def post_login_page(request: Request,
                          username: Annotated[str, Form()],
                          password: Annotated[str, Form()],
                          db: Annotated[Session, Depends(get_db)]):
    global curr_user
    error = {}
    if curr_user is None:
        check_user = db.scalars(select(Buyer).where(Buyer.name == username)).first()
        if check_user is None:
            error.update({'error': 'Такого пользователя не существует'})
        elif check_user.password != password:
            error.update({'error': 'Неверный пароль'})
        else:
            curr_user = check_user
            return RedirectResponse('/', status_code=302)

    context = {
        'request': request,
        'error': error,
        'user': curr_user,
    }
    return templates.TemplateResponse('login_page.html', context=context)


@app.get('/purchased_applications')
async def get_purchased_applications(request: Request,
                                     db: Annotated[Session, Depends(get_db)],
                                     page: int = 1,) -> HTMLResponse:
    global curr_user
    games = []
    error = {}
    if curr_user:
        curr_user = db.get(Buyer, curr_user.id)
        games = curr_user.buyers_game
    else:
        error.update({'error': 'Вы не авторизованы. Пожалуйста, войдите в аккаунт или зарегистрируйтесь.'})

    params = Params(size=5, page=page)
    paginated_games = paginate(games, params)
    context = {
        'request': request,
        'user': curr_user,
        'paginator': paginated_games,
        'page_obj': {
            'items': paginated_games.items,
            'number': paginated_games.page,
            'has_other_pages': True if paginated_games.pages > 1 else False,
            'has_previous': True if paginated_games.page - 1 > 0 else False,
            'has_next': True if paginated_games.page + 1 <= paginated_games.pages else False,
            'paginator': {'page_range': range(1, paginated_games.pages + 1)},
            'previous_page_number': paginated_games.page - 1,
            'next_page_number': paginated_games.page + 1,
        },
        'error': error,
        'size': paginated_games.size,
    }
    return templates.TemplateResponse('users_game_page.html', context=context)


@app.get('/shop/')
async def get_shop_page(request: Request,
                        db: Annotated[Session, Depends(get_db)],
                        page: int = 1, size: int = 3) -> HTMLResponse:
    global curr_user
    games = db.scalars(select(Game)).all()
    params = Params(size=size, page=page)
    paginated_games = paginate(games, params)

    if page > paginated_games.pages:
        paginated_games = paginate(games, Params(size=size, page=paginated_games.pages))

    context = {
        'request': request,
        'user': curr_user,
        'paginator': paginated_games,
        'page_obj': {
            'items': paginated_games.items,
            'number': paginated_games.page,
            'has_other_pages': True if paginated_games.pages > 1 else False,
            'has_previous': True if paginated_games.page-1 > 0 else False,
            'has_next': True if paginated_games.page+1 <= paginated_games.pages else False,
            'paginator': {'page_range': range(1, paginated_games.pages+1)},
            'previous_page_number': paginated_games.page-1,
            'next_page_number': paginated_games.page+1,
        },
        'size': paginated_games.size,
        'info': {},
    }
    return templates.TemplateResponse('shop_page.html', context=context)


@app.post('/shop/')
async def post_shop_page(request: Request,
                         db: Annotated[Session, Depends(get_db)],
                         game_id: Annotated[int, Form()],
                         size: int = 3, page: int = 1) -> HTMLResponse:
    global curr_user
    game = db.scalars(select(Game).where(Game.id == game_id)).first()
    games = db.scalars(select(Game)).all()
    info = {}
    error = {}
    params = Params(size=int(size), page=page)
    paginated_games = paginate(games, params)

    if page > paginated_games.pages:
        paginated_games = paginate(games, Params(size=size, page=paginated_games.pages))

    if not curr_user:
        error.update({'error': 'Войдите в аккаунт или зарегистрируйтесь!'})
    else:
        curr_user = db.get(Buyer, curr_user.id)
        if curr_user.balance < game.cost:
            error.update({'error': 'Недостаточно средств'})
        elif game.age_limited and curr_user.age < 18:
            error.update({'error': 'Вы не достигли возраста покупки'})
        elif game in curr_user.buyers_game:
            error.update({'error': 'У Вас уже куплена эта игра'})
        else:
            info.update({'message': f'{game.title} куплена!'})
            curr_user.balance -= game.cost
            curr_user.buyers_game.append(game)
            db.commit()

    context = {
        'request': request,
        'user': curr_user,
        'paginator': paginated_games,
        'page_obj': {
            'items': paginated_games.items,
            'number': paginated_games.page,
            'has_other_pages': True if paginated_games.pages > 1 else False,
            'has_previous': True if paginated_games.page-1 > 0 else False,
            'has_next': True if paginated_games.page+1 <= paginated_games.pages else False,
            'paginator': {'page_range': range(1, paginated_games.pages+1)},
            'previous_page_number': paginated_games.page-1,
            'next_page_number': paginated_games.page+1,
        },
        'size': paginated_games.size,
        'info': {},
        'error': error,
    }
    return templates.TemplateResponse('shop_page.html', context=context)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
