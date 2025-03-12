from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.racing import RaceCard
from app.models.horse import Horse
from app.models.jockey import Jockey
from app.models.result import HorseResult
from app.models.trainer import Trainer
from app.models.course import Course
from app.models.embedding import (
    RaceCardEmbedding, HorseEmbedding, JockeyEmbedding,
    TrainerEmbedding, CourseEmbedding
)
from app.utils.embedding import generate_embedding
from app.core.logging import logger

def vectorize_racecard(db: Session, racecard: RaceCard) -> None:
    """Create rich embeddings for a racecard incorporating all relevant race information"""
    
    # Create comprehensive text representation
    text_components = [
        f"Race: {racecard.race_name} at {racecard.course}",
        f"Date: {racecard.date}",
        f"Distance: {racecard.distance}",
        f"Going: {racecard.going}",
        f"Surface: {racecard.surface}",
        f"Class: {racecard.race_class}",
        f"Type: {racecard.race_type}",
        f"Prize: {racecard.prize}",
        "Runners:",
    ]

    # Add runner information
    runners = racecard.raw_data.get("runners", []) if racecard.raw_data else []
    for runner in runners:
        runner_info = [
            f"Horse: {runner.get('horse', 'N/A')}",
            f"Recent Form: {runner.get('form', 'N/A')}",
            f"Jockey: {runner.get('jockey', 'N/A')}",
            f"Trainer: {runner.get('trainer', 'N/A')}",
            f"Weight: {runner.get('weight', 'N/A')}",
            f"Draw: {runner.get('draw', 'N/A')}",
            f"Official Rating: {runner.get('or', 'N/A')}",
        ]
        text_components.extend(runner_info)

    comprehensive_text = "\n".join(text_components)
    
    # Generate embedding
    embedding_vector = generate_embedding(comprehensive_text)
    if embedding_vector:
        embedding = RaceCardEmbedding(
            race_id=racecard.race_id,
            embedding=embedding_vector,
            last_updated=datetime.utcnow(),
            metadata={
                "runner_count": len(runners),
                "race_type": racecard.race_type,
                "race_class": racecard.race_class,
                "is_big_race": racecard.big_race
            }
        )
        db.merge(embedding)

def vectorize_horse(db: Session, horse: Horse) -> None:
    """Create embeddings for horse information including form and statistics"""
    
    text_components = [
        f"Horse: {horse.name}",
        f"Profile: {horse.age} year old {horse.sex} {horse.colour}",
        f"Region: {horse.region}",
        f"Breeding: By {horse.sire} out of {horse.dam} ({horse.damsire})",
        f"Connections: Trained by {horse.trainer}, owned by {horse.owner}",
        f"Form: {horse.form}",
        f"Last Run: {horse.last_run}"
    ]
    
    # Add detailed race history from results relationship
    if horse.results:
        text_components.append("Recent Results:")
        for result in sorted(horse.results, key=lambda x: x.race.date, reverse=True)[:5]:
            text_components.append(
                f"- {result.position} of {result.race.field_size} "
                f"at {result.race.course} ({result.race.distance})"
            )

    comprehensive_text = "\n".join(text_components)
    
    embedding_vector = generate_embedding(comprehensive_text)
    if embedding_vector:
        embedding = HorseEmbedding(
            horse_id=horse.horse_id,
            embedding=embedding_vector,
            last_updated=datetime.utcnow(),
            metadata={
                "age": horse.age,
                "sex": horse.sex,
                "rating": horse.raw_data.get("official_rating") if horse.raw_data else None
            }
        )
        db.merge(embedding)

def vectorize_jockey(db: Session, jockey: Jockey) -> None:
    """Create embeddings for jockey information including statistics and performance records"""
    
    # Get all results where this jockey rode
    results = db.query(HorseResult).filter(
        HorseResult.jockey_id == jockey.jockey_id
    ).order_by(HorseResult.race.date.desc()).all()
    
    text_components = [
        f"Jockey: {jockey.name}",
        f"ID: {jockey.jockey_id}",
    ]
    
    if jockey.raw_data:
        # Add career statistics if available
        stats = jockey.raw_data.get("statistics", {})
        if stats:
            text_components.extend([
                "Career Statistics:",
                f"Total Rides: {stats.get('total_rides', 'N/A')}",
                f"Wins: {stats.get('wins', 'N/A')}",
                f"Win Rate: {stats.get('win_percentage', 'N/A')}%",
                f"Places: {stats.get('places', 'N/A')}",
                f"Place Rate: {stats.get('place_percentage', 'N/A')}%"
            ])
    
    # Add recent form (last 20 rides)
    if results:
        text_components.append("\nRecent Form:")
        for result in results[:20]:
            text_components.append(
                f"- {result.position} on {result.horse.name} "
                f"at {result.race.course} ({result.race.race_class})"
            )
    
    # Add course specialties
    course_stats = {}
    for result in results:
        if result.position == "1":  # Count wins by course
            course = result.race.course
            course_stats[course] = course_stats.get(course, 0) + 1
    
    if course_stats:
        text_components.append("\nCourse Specialties:")
        for course, wins in sorted(course_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            text_components.append(f"- {course}: {wins} wins")
    
    comprehensive_text = "\n".join(text_components)
    
    embedding_vector = generate_embedding(comprehensive_text)
    if embedding_vector:
        embedding = JockeyEmbedding(
            jockey_id=jockey.jockey_id,
            embedding=embedding_vector,
            last_updated=datetime.utcnow(),
            metadata={
                "total_rides": len(results),
                "wins": len([r for r in results if r.position == "1"]),
                "places": len([r for r in results if r.position in ["1", "2", "3"]])
            }
        )
        db.merge(embedding)

def vectorize_trainer(db: Session, trainer: Trainer) -> None:
    """Create embeddings for trainer information including statistics and performance records"""
    
    # Get all results for horses trained by this trainer
    results = db.query(HorseResult).filter(
        HorseResult.trainer_id == trainer.trainer_id
    ).order_by(HorseResult.race.date.desc()).all()
    
    text_components = [
        f"Trainer: {trainer.name}",
        f"ID: {trainer.trainer_id}",
    ]
    
    if trainer.raw_data:
        # Add stable statistics if available
        stats = trainer.raw_data.get("statistics", {})
        if stats:
            text_components.extend([
                "Stable Statistics:",
                f"Total Runners: {stats.get('total_runners', 'N/A')}",
                f"Winners: {stats.get('winners', 'N/A')}",
                f"Strike Rate: {stats.get('strike_rate', 'N/A')}%",
                f"Prize Money: {stats.get('prize_money', 'N/A')}"
            ])
    
    # Add recent form (last 20 runners)
    if results:
        text_components.append("\nRecent Form:")
        for result in results[:20]:
            text_components.append(
                f"- {result.horse.name}: {result.position} "
                f"at {result.race.course} ({result.race.race_type})"
            )
    
    # Add course and race type analysis
    course_stats = {}
    type_stats = {}
    for result in results:
        if result.position == "1":
            course = result.race.course
            race_type = result.race.race_type
            course_stats[course] = course_stats.get(course, 0) + 1
            type_stats[race_type] = type_stats.get(race_type, 0) + 1
    
    if course_stats:
        text_components.append("\nBest Courses:")
        for course, wins in sorted(course_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            text_components.append(f"- {course}: {wins} wins")
    
    if type_stats:
        text_components.append("\nBest Race Types:")
        for type_, wins in sorted(type_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            text_components.append(f"- {type_}: {wins} wins")
    
    comprehensive_text = "\n".join(text_components)
    
    embedding_vector = generate_embedding(comprehensive_text)
    if embedding_vector:
        embedding = TrainerEmbedding(
            trainer_id=trainer.trainer_id,
            embedding=embedding_vector,
            last_updated=datetime.utcnow(),
            metadata={
                "total_runners": len(results),
                "winners": len([r for r in results if r.position == "1"]),
                "types": list(type_stats.keys())
            }
        )
        db.merge(embedding)

def vectorize_course(db: Session, course: Course) -> None:
    """Create embeddings for course information including characteristics and statistics"""
    
    # Get recent results at this course
    results = db.query(HorseResult).join(RaceCard).filter(
        RaceCard.course_id == course.course_id
    ).order_by(RaceCard.date.desc()).all()
    
    text_components = [
        f"Course: {course.name}",
        f"ID: {course.course_id}",
    ]
    
    if course.raw_data:
        # Add course characteristics
        characteristics = course.raw_data.get("characteristics", {})
        if characteristics:
            text_components.extend([
                "Course Characteristics:",
                f"Track Type: {characteristics.get('track_type', 'N/A')}",
                f"Configuration: {characteristics.get('configuration', 'N/A')}",
                f"Surface: {characteristics.get('surface', 'N/A')}",
                f"Length: {characteristics.get('length', 'N/A')}",
                f"Run-In: {characteristics.get('run_in', 'N/A')}"
            ])
    
    # Add recent race analysis
    if results:
        # Analyze winning running styles
        running_styles = {}
        for result in results:
            if result.position == "1":
                style = "Front Runner" if "made all" in (result.comment or "").lower() else \
                        "Hold Up" if "held up" in (result.comment or "").lower() else "Mid Pack"
                running_styles[style] = running_styles.get(style, 0) + 1
        
        if running_styles:
            text_components.append("\nWinning Running Styles:")
            for style, count in running_styles.items():
                text_components.append(f"- {style}: {count} wins")
    
    # Add draw bias analysis for flat races
    flat_results = [r for r in results if r.race.jumps != "true"]
    if flat_results:
        draw_stats = {}
        for result in flat_results:
            if result.position == "1" and result.draw:
                draw_stats[result.draw] = draw_stats.get(result.draw, 0) + 1
        
        if draw_stats:
            text_components.append("\nDraw Bias Analysis:")
            for draw, wins in sorted(draw_stats.items(), key=lambda x: int(x[0])):
                text_components.append(f"- Draw {draw}: {wins} wins")
    
    comprehensive_text = "\n".join(text_components)
    
    embedding_vector = generate_embedding(comprehensive_text)
    if embedding_vector:
        embedding = CourseEmbedding(
            course_id=course.course_id,
            embedding=embedding_vector,
            last_updated=datetime.utcnow(),
            metadata={
                "surface": course.raw_data.get("surface"),
                "track_type": course.raw_data.get("track_type"),
                "region_codes": course.region_codes
            }
        )
        db.merge(embedding)

def vectorize_all():
    """Vectorize all entities in the database"""
    db = SessionLocal()
    try:
        # Vectorize racecards
        logger.info("Vectorizing racecards...")
        racecards = db.query(RaceCard).all()
        for rc in racecards:
            vectorize_racecard(db, rc)
        
        # Vectorize horses
        logger.info("Vectorizing horses...")
        horses = db.query(Horse).all()
        for horse in horses:
            vectorize_horse(db, horse)
        
        # Vectorize jockeys
        logger.info("Vectorizing jockeys...")
        jockeys = db.query(Jockey).all()
        for jockey in jockeys:
            vectorize_jockey(db, jockey)
        
        # Vectorize trainers
        logger.info("Vectorizing trainers...")
        trainers = db.query(Trainer).all()
        for trainer in trainers:
            vectorize_trainer(db, trainer)
        
        # Vectorize courses
        logger.info("Vectorizing courses...")
        courses = db.query(Course).all()
        for course in courses:
            vectorize_course(db, course)
        
        # Commit all changes
        db.commit()
        logger.info("Vectorization completed successfully")
        
    except Exception as e:
        logger.error(f"Error during vectorization: {e}")
        db.rollback()
    finally:
        db.close()
