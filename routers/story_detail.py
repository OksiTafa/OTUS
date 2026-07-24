from fastapi import APIRouter, Query, HTTPException, status


from schemas.stories import Stories, story_list


router = APIRouter()


@router.get("/", response_model=list[Stories])
async def get_stories_list(
        title: str = Query(None, description="Заголовок"),
        description: str = Query(None, description="Описание"),
        full_text: str = Query(None, description="История целиком")
):
    """Получить список историй."""
    result = story_list

    if title is not None:
        result = [movie for movie in result if movie.title == title]
    if description is not None:
        result = [movie for movie in result if movie.description == description]
    if full_text is not None:
        result = [movie for movie in result if movie.full_text == full_text]

    return result


@router.get("/{story_id}/", response_model=Stories)
async def story_detail(story_id: int):
    """Получить подробную информацию об истории."""
    story_id -= 1

    if story_id < 0 or story_id >= len(story_list):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="История не найдена")

    return story_list[story_id]


@router.post("/catalog/", response_model=Stories, status_code=status.HTTP_201_CREATED)
async def movie_create(stories: Stories):
    """Добавить историю."""
    for m in story_list:
        if m.title == stories.title and m.description == stories.description:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Такая история уже есть")

    story_list.append(stories)

    return story_list


@router.put("/{story_id}/", response_model=Stories)
async def movie_update(story_id: int, story: Stories):
    """Обновить историю."""
    story_id -= 1

    if story_id < 0 or story_id >= len(story_list):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")

    story_list[story_id].title = story.title
    story_list[story_id].description = story.description
    story_list[story_id].full_text = story.full_text

    return story_list[story_id]


@router.delete("/{story_id}/")
async def movie_delete(story_id: int):
    """Удалить фильм."""
    story_id -= 1

    if story_id < 0 or story_id >= len(story_list):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    result = story_list.pop(story_id)

    return {'message': f'История {result.title} была удалена'}
