from fastapi import APIRouter, Query, HTTPException, status, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from schemas.stories import story_list

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def html_catalog_story(
        request: Request,
        title: str = Query(None, title = "Название истории"),
        description: str = Query(None, descroption = "Краткое описание истории"),
        full_text: str = Query(None, descroption = "История целиком")
):
    # получим список историй
    result = story_list

    if title is not None:
        result = [story for story in result if story.title == title]

    if description is not None:
        result = [story for story in result if story.description == description]

    if full_text is not None:
        result = [story for story in result if story.full_text == full_text]

    context = {"stories": result, "title": "Список историй"}
    return templates.TemplateResponse(request, "catalog/catalog.html", context=context)


@router.get("/{story_id}", response_class=HTMLResponse, name="html_story_det")
async def html_story_det(request: Request, story_id: int):
    """Получить подробную информацию об истории"""
    story_id -= 1

    if story_id < 0 or story_id >= len(story_list):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="История не найдена")

    # Генерируем пути к фото
    photos = [
        f"/src/{story_id + 1}/photo1.jpg",
        f"/src/{story_id + 1}/photo2.jpg",
        f"/src/{story_id + 1}/photo3.jpg",
        f"/src/{story_id + 1}/photo4.jpg",
        f"/src/{story_id + 1}/photo5.jpg",
        f"/src/{story_id + 1}/photo6.jpg",
        f"/src/{story_id + 1}/preview.jpg",
    ]

    context = {"story": story_list[story_id], "photos": photos}

    return templates.TemplateResponse(request, "catalog/story_detail.html", context=context)
