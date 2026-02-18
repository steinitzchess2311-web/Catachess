import { useReducer, useCallback } from 'react';
import { parseFen, validateFen, STARTING_FEN } from '../../chessJS/fen';
import {
  EditorPiece,
  CastlingToggles,
  EMPTY_BOARD_FEN,
  placePiece,
  removePiece,
  movePiece,
  setTurn,
  setCastling,
  setEnPassant,
  getPieceAt,
  computeAvailableCastling,
  castlingToString,
  parseCastlingString,
  restrictCastlingToAvailable,
} from './fenManipulation';

export type Selected = 'pointer' | 'trash' | EditorPiece;

interface EditorState {
  fen: string;
  selected: Selected;
  orientation: 'white' | 'black';
}

type EditorAction =
  | { type: 'SET_FEN'; fen: string }
  | { type: 'SET_SELECTED'; selected: Selected }
  | { type: 'PLACE_PIECE'; square: string; piece: EditorPiece }
  | { type: 'REMOVE_PIECE'; square: string }
  | { type: 'MOVE_PIECE'; from: string; to: string }
  | { type: 'TOGGLE_COLOR'; square: string }
  | { type: 'SET_TURN'; turn: 'w' | 'b' }
  | { type: 'SET_CASTLING'; castling: CastlingToggles }
  | { type: 'SET_EN_PASSANT'; ep: string }
  | { type: 'FLIP_BOARD' }
  | { type: 'CLEAR_BOARD' }
  | { type: 'RESET_TO_START' };

function reducer(state: EditorState, action: EditorAction): EditorState {
  switch (action.type) {
    case 'SET_FEN': {
      if (!parseFen(action.fen)) return state;
      return { ...state, fen: action.fen };
    }
    case 'SET_SELECTED':
      return { ...state, selected: action.selected };
    case 'PLACE_PIECE': {
      const newFen = restrictCastlingToAvailable(
        placePiece(state.fen, action.square, action.piece)
      );
      return { ...state, fen: newFen };
    }
    case 'REMOVE_PIECE': {
      const newFen = restrictCastlingToAvailable(
        removePiece(state.fen, action.square)
      );
      return { ...state, fen: newFen };
    }
    case 'MOVE_PIECE': {
      const newFen = restrictCastlingToAvailable(
        movePiece(state.fen, action.from, action.to)
      );
      return { ...state, fen: newFen };
    }
    case 'TOGGLE_COLOR': {
      const piece = getPieceAt(state.fen, action.square);
      if (!piece) return state;
      const toggled: EditorPiece = { ...piece, color: piece.color === 'w' ? 'b' : 'w' };
      const newFen = restrictCastlingToAvailable(
        placePiece(state.fen, action.square, toggled)
      );
      return { ...state, fen: newFen };
    }
    case 'SET_TURN':
      return { ...state, fen: setTurn(state.fen, action.turn) };
    case 'SET_CASTLING':
      return { ...state, fen: setCastling(state.fen, castlingToString(action.castling)) };
    case 'SET_EN_PASSANT':
      return { ...state, fen: setEnPassant(state.fen, action.ep) };
    case 'FLIP_BOARD':
      return { ...state, orientation: state.orientation === 'white' ? 'black' : 'white' };
    case 'CLEAR_BOARD':
      return { ...state, fen: EMPTY_BOARD_FEN };
    case 'RESET_TO_START':
      return { ...state, fen: STARTING_FEN };
    default:
      return state;
  }
}

function initialState(): EditorState {
  return {
    fen: STARTING_FEN,
    selected: 'pointer',
    orientation: 'white',
  };
}

export function useBoardEditor() {
  const [state, dispatch] = useReducer(reducer, undefined, initialState);

  const parts = parseFen(state.fen);
  const validation = validateFen(state.fen);
  const legalFen = validation.valid ? state.fen : undefined;

  const turn: 'w' | 'b' = parts?.turn ?? 'w';
  const castling = parseCastlingString(parts?.castling ?? '-');
  const enPassant = parts?.enPassant ?? '-';
  const availableCastling = computeAvailableCastling(state.fen);

  const setFen = useCallback((fen: string) => dispatch({ type: 'SET_FEN', fen }), []);
  const setSelected = useCallback((s: Selected) => dispatch({ type: 'SET_SELECTED', selected: s }), []);

  const onSquareClick = useCallback((square: string) => {
    const { selected } = state;
    if (selected === 'pointer') return; // pointer mode uses drag only
    if (selected === 'trash') {
      dispatch({ type: 'REMOVE_PIECE', square });
    } else {
      // Piece placement mode
      const piece = selected as EditorPiece;
      const existing = getPieceAt(state.fen, square);
      if (existing && existing.color === piece.color && existing.type === piece.type) {
        dispatch({ type: 'REMOVE_PIECE', square }); // toggle off
      } else {
        dispatch({ type: 'PLACE_PIECE', square, piece });
      }
    }
  }, [state]);

  const onSquareRightClick = useCallback((square: string) => {
    dispatch({ type: 'TOGGLE_COLOR', square });
  }, []);

  const onPieceDrop = useCallback((_from: string, _to: string, _piece: string): boolean => {
    dispatch({ type: 'MOVE_PIECE', from: _from, to: _to });
    return true;
  }, []);

  const onPieceDropOffBoard = useCallback((square: string) => {
    dispatch({ type: 'REMOVE_PIECE', square });
  }, []);

  // react-chessboard SparePiece drag → board drop  ("wQ", "e4")
  const onSparePieceDrop = useCallback((piece: string, square: string): boolean => {
    const color = piece[0] as PieceColor;
    const type = piece[1].toLowerCase() as PieceType;
    dispatch({ type: 'PLACE_PIECE', square, piece: { color, type } });
    return true;
  }, []);

  const setTurnAction = useCallback((t: 'w' | 'b') => dispatch({ type: 'SET_TURN', turn: t }), []);
  const setCastlingAction = useCallback((c: CastlingToggles) => dispatch({ type: 'SET_CASTLING', castling: c }), []);
  const setEnPassantAction = useCallback((ep: string) => dispatch({ type: 'SET_EN_PASSANT', ep }), []);
  const flipBoard = useCallback(() => dispatch({ type: 'FLIP_BOARD' }), []);
  const clearBoard = useCallback(() => dispatch({ type: 'CLEAR_BOARD' }), []);
  const resetToStart = useCallback(() => dispatch({ type: 'RESET_TO_START' }), []);

  return {
    fen: state.fen,
    legalFen,
    selected: state.selected,
    orientation: state.orientation,
    turn,
    castling,
    enPassant,
    availableCastling,
    setFen,
    setSelected,
    onSquareClick,
    onSquareRightClick,
    onPieceDrop,
    onPieceDropOffBoard,
    onSparePieceDrop,
    setTurnAction,
    setCastlingAction,
    setEnPassantAction,
    flipBoard,
    clearBoard,
    resetToStart,
  };
}
